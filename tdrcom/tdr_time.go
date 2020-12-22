package tdrcom

import (
	"fmt"
	"time"
)

func DatetimeToUint64(str string) uint64 {
	t, _ := time.Parse("2006-01-02 15:04:05", str)
	return (uint64(t.Hour()) << 32 & 0x0000FFFF00000000) | (uint64(t.Minute()) << 48 & 0x00FF000000000000) | (uint64(t.Second()) << 56 & 0xFF00000000000000) |
		(uint64(t.Year()) & 0x000000000000FFFF) | (uint64(t.Month()) << 16 & 0x0000000000FF0000) | (uint64(t.Day()) << 24 & 0x00000000FF000000)
}

func Uint64ToDatetime(num uint64) string {
	return fmt.Sprintf("%d-%02d-%02d %02d:%02d:%02d", uint16(num&0x000000000000FFFF), uint8(num&0x0000000000FF0000>>16), uint8(num&0x00000000FF000000>>24),
		uint16(num&0x0000FFFF00000000>>32), uint8(num&0x00FF000000000000>>48), uint8(num&0xFF00000000000000>>56))
}

func DateToUint(str string) uint32 {
	t, _ := time.Parse("2006-01-02", str)
	return (uint32(t.Year()) & 0x0000FFFF) | (uint32(t.Month()) << 16 & 0x00FF0000) | (uint32(t.Day()) << 24 & 0xFF000000)
}

func UintToDate(num uint32) string {
	return fmt.Sprintf("%d-%02d-%02d", uint16(num&0x0000FFFF), uint8(num&0x00FF0000>>16), uint8(num&0xFF000000>>24))
}

func TimeToUint(str string) uint32 {
	t, _ := time.Parse("15:04:05", str)
	return (uint32(t.Hour()) & 0x0000FFFF) | (uint32(t.Minute()) << 16 & 0x00FF0000) | (uint32(t.Second()) << 24 & 0xFF000000)
}

func UintToTime(num uint32) string {
	return fmt.Sprintf("%d:%02d:%02d", uint16(num&0x0000FFFF), uint8(num&0x00FF0000>>16), uint8(num&0xFF000000>>24))
}
