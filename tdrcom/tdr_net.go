package tdrcom

import (
	"net"
	"strconv"
)

func IpToUint(ip string) uint32 {
	ipSlice := net.ParseIP(ip).To4()
	return uint32(ipSlice[3])<<24 | uint32(ipSlice[2])<<16 | uint32(ipSlice[1])<<8 | uint32(ipSlice[0])
}

func UintToIp(ipInt uint32) string {
	p0 := strconv.FormatUint(uint64(ipInt&0x000000ff), 10)
	p1 := strconv.FormatUint(uint64(ipInt&0x0000ff00>>8), 10)
	p2 := strconv.FormatUint(uint64(ipInt&0x00ff0000>>16), 10)
	p3 := strconv.FormatUint(uint64(ipInt&0xff000000>>24), 10)
	return p0 + "." + p1 + "." + p2 + "." + p3
}
