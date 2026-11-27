/* SPDX-License-Identifier: MPL-2.0
 * Headless mGBA host for a single GBA linked to a WonderSwan UART.
 * This file is included by the pinned core's io.c; only UART MMIO is extended.
 */
#include <mgba/core/core.h>
#include <mgba/core/log.h>
#include <mgba/core/blip_buf.h>
#include <mgba/gba/core.h>
#include <mgba-util/vfs.h>

#define LINK_API __declspec(dllexport)
struct ByteFIFO {
    uint8_t data[4];
    unsigned first, count;
};
static struct mCore* linkCore;
static struct mStandardLogger logger;
static struct ByteFIFO sendFIFO, receiveFIFO;
static uint64_t sendDue, elapsed;
static uint32_t clockSample;

/* The libretro core tracks its master clock in 32 bits. Sample every host step. */
static uint64_t serialClock(struct mTiming* timing) {
    uint32_t current = mTimingCurrentTime(timing);
    elapsed += (uint32_t)(current - clockSample);
    clockSample = current;
    return elapsed;
}
static bool receiveError;
static color_t video[240 * 160];

static bool fifoPush(struct ByteFIFO* fifo, unsigned capacity, uint8_t value) {
    if (fifo->count >= capacity) return false;
    fifo->data[(fifo->first + fifo->count) % 4] = value;
    ++fifo->count;
    return true;
}
static int fifoPop(struct ByteFIFO* fifo) {
    if (!fifo->count) return -1;
    int value = fifo->data[fifo->first];
    fifo->first = (fifo->first + 1) % 4;
    --fifo->count;
    return value;
}
static unsigned fifoCapacity(struct GBA* gba) {
    return gba->sio.siocnt & 0x100 ? 4 : 1;
}
static unsigned byteCycles(struct GBA* gba) {
    static const unsigned baud[4] = {9600, 38400, 57600, 115200};
    return (16777216 * 10 + baud[gba->sio.siocnt & 3] - 1) / baud[gba->sio.siocnt & 3];
}
static void uartReset(void) {
    sendFIFO = (struct ByteFIFO){0};
    receiveFIFO = (struct ByteFIFO){0};
    receiveError = false;
}
static bool uartWrite(struct GBA* gba, uint32_t address, uint16_t value) {
    if (address == REG_RCNT && (value & 0xC000)) uartReset();
    if (address == REG_SIOCNT) {
        if (gba->sio.mode != SIO_UART || (value & 0x3000) != 0x3000) uartReset();
        if (!(value & 0x0400)) sendFIFO.count = 0;
        if (!(value & 0x0800)) receiveFIFO.count = 0;
    }
    if (gba->sio.mode != SIO_UART || address != REG_SIOMLT_SEND) return false;
    if (gba->sio.siocnt & 0x0400) {
        if (!sendFIFO.count) sendDue = serialClock(&gba->timing) + byteCycles(gba);
        fifoPush(&sendFIFO, fifoCapacity(gba), value);
    }
    return true;
}
static bool uartRead(struct GBA* gba, uint32_t address, uint16_t* value) {
    if (gba->sio.mode != SIO_UART) return false;
    if (address == REG_SIOCNT) {
        *value = (gba->sio.siocnt & ~0x70) | (sendFIFO.count >= fifoCapacity(gba) ? 0x10 : 0)
               | (receiveFIFO.count ? 0 : 0x20) | (receiveError ? 0x40 : 0);
        receiveError = false;
        return true;
    }
    if (address != REG_SIOMLT_SEND) return false;
    int byte = fifoPop(&receiveFIFO);
    *value = byte < 0 ? 0 : byte;
    return true;
}
LINK_API int cable_gba_send(void) {
    struct GBA* gba = linkCore->board;
    if (!sendFIFO.count || serialClock(&gba->timing) < sendDue) return -1;
    sendDue += byteCycles(gba);
    return fifoPop(&sendFIFO);
}
LINK_API int cable_gba_receive(unsigned byte) {
    struct GBA* gba = linkCore->board;
    if (gba->sio.mode != SIO_UART || !(gba->sio.siocnt & 0x0800)) return 0;
    if (fifoPush(&receiveFIFO, fifoCapacity(gba), byte)) return 1;
    receiveError = true;
    return -1;
}
LINK_API void cable_gba_close(void) {
    if (!linkCore) return;
    mCoreConfigDeinit(&linkCore->config);
    linkCore->deinit(linkCore);
    linkCore = NULL;
    mLogSetDefaultLogger(NULL);
    mStandardLoggerDeinit(&logger);
}
LINK_API int cable_gba_open(const void* rom, size_t size, const void* save, size_t saveSize) {
    if (linkCore || !rom || !size || sizeof(color_t) != 2) return 0;
    mStandardLoggerInit(&logger);
    logger.logToStdout = false;
    mLogSetDefaultLogger(&logger.d);
    linkCore = GBACoreCreate();
    if (!linkCore || !linkCore->init(linkCore)) return 0;
    mCoreInitConfig(linkCore, "darklink");
    linkCore->setVideoBuffer(linkCore, video, 240);
    linkCore->setAudioBufferSize(linkCore, 2048);
    for (unsigned i = 0; i < 2; ++i)
        blip_set_rates(linkCore->getAudioChannel(linkCore, i), linkCore->frequency(linkCore), 44100);
    struct VFile* vf = VFileMemChunk(rom, size);
    if (!vf || !linkCore->loadROM(linkCore, vf)) {
        if (vf) vf->close(vf);
        cable_gba_close();
        return 0;
    }
    linkCore->reset(linkCore);
    clockSample = mTimingCurrentTime(linkCore->timing);
    elapsed = 0;
    uartReset();
    if (saveSize && !linkCore->savedataRestore(linkCore, save, saveSize, true)) {
        cable_gba_close();
        return 0;
    }
    return 1;
}
LINK_API void cable_gba_until(uint64_t deadline) {
    while (serialClock(linkCore->timing) < deadline) linkCore->runLoop(linkCore);
}
LINK_API uint64_t cable_gba_clock(void) { return serialClock(linkCore->timing); }
LINK_API unsigned cable_gba_frame(void) { return linkCore->frameCounter(linkCore); }
LINK_API void cable_gba_keys(unsigned keys) { linkCore->setKeys(linkCore, keys); }
LINK_API const color_t* cable_gba_pixels(void) { return video; }
LINK_API int cable_gba_audio(int16_t* out, int frames) {
    blip_t* left = linkCore->getAudioChannel(linkCore, 0);
    blip_t* right = linkCore->getAudioChannel(linkCore, 1);
    int count = blip_read_samples(left, out, frames, 1);
    blip_read_samples(right, out + 1, count, 1);
    return count;
}
LINK_API int cable_gba_read16(uint32_t address) { return linkCore->busRead16(linkCore, address); }
LINK_API size_t cable_gba_save(uint8_t* out, size_t capacity) {
    void* data = NULL;
    size_t len = linkCore->savedataClone(linkCore, &data);
    if (data && len <= capacity) memcpy(out, data, len);
    free(data);
    return len;
}
