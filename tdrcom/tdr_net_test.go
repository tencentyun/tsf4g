package tdrcom

import (
	"testing"
)

func TestIpToUint(t *testing.T) {
	type args struct {
		ip string
	}
	tests := []struct {
		name string
		args args
		want uint32
	}{
		{
			args: args{"192.168.0.1"},
			want: 16820416,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := IpToUint(tt.args.ip); got != tt.want {
				t.Errorf("IpToUint() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestUintToIp(t *testing.T) {
	type args struct {
		ipInt uint32
	}
	tests := []struct {
		name string
		args args
		want string
	}{
		{
			args: args{16820416},
			want: "192.168.0.1",
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := UintToIp(tt.args.ipInt); got != tt.want {
				t.Errorf("UintToIp() = %v, want %v", got, tt.want)
			}
		})
	}
}
