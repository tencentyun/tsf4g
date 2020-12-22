package tdrcom

import (
	"testing"
)

func TestDateToUint(t *testing.T) {
	type args struct {
		date string
	}
	tests := []struct {
		name string
		args args
		want uint32
	}{
		{
			args: args{
				"2014-03-28",
			},
			want: 469960670,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := DateToUint(tt.args.date); got != tt.want {
				t.Errorf("DateToUint() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestTimeToUint(t *testing.T) {
	type args struct {
		str string
	}
	tests := []struct {
		name string
		args args
		want uint32
	}{
		{
			args: args{
				"13:11:56",
			},
			want: 940245005,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := TimeToUint(tt.args.str); got != tt.want {
				t.Errorf("TimeToUint() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestDatetimeToUint64(t *testing.T) {
	type args struct {
		str string
	}
	tests := []struct {
		name string
		args args
		want uint64
	}{
		{
			args: args{
				"2014-04-01 13:30:59",
			},
			want: 4259842353390684126,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := DatetimeToUint64(tt.args.str); got != tt.want {
				t.Errorf("DatetimeToUint64() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestUint64ToDatetime(t *testing.T) {
	type args struct {
		num uint64
	}
	tests := []struct {
		name string
		args args
		want string
	}{
		{
			args: args{
				4259842353390684126,
			},
			want: "2014-04-01 13:30:59",
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := Uint64ToDatetime(tt.args.num); got != tt.want {
				t.Errorf("Uint64ToDatetime() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestUintToDate(t *testing.T) {
	type args struct {
		num uint32
	}
	tests := []struct {
		name string
		args args
		want string
	}{
		{
			args: args{
				469960670,
			},
			want: "2014-03-28",
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := UintToDate(tt.args.num); got != tt.want {
				t.Errorf("UintToDate() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestUintToTime(t *testing.T) {
	type args struct {
		num uint32
	}
	tests := []struct {
		name string
		args args
		want string
	}{
		{
			args: args{
				940245005,
			},
			want: "13:11:56",
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := UintToTime(tt.args.num); got != tt.want {
				t.Errorf("UintToTime() = %v, want %v", got, tt.want)
			}
		})
	}
}
