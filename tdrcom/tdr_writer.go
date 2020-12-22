package tdrcom

import (
	"errors"
	"io"
)

// smallBufferSize is an initial allocation minimal capacity.
const smallBufferSize = 64
const maxInt = int(^uint(0) >> 1)

// Writer implements io.Writer, io.Seeker
type Writer struct {
	s []byte
	i int // current writing index
}

// Bytes return the writen content
func (w *Writer) Bytes() []byte {
	return w.s[:w.i]
}

// Tell return the seek position
func (w *Writer) Tell() int64 {
	return int64(w.i)
}

// Write the contents of p to the slice, growing the slice as
// needed. The return value n is the writen size; err is always nil.
// If the buffer becomes too large, Write will panic with ErrTooLarge.
func (w *Writer) Write(p []byte) (n int, err error) {
	w.tryGrow(len(p))
	size := copy(w.s[w.i:], p)
	w.i += size
	return size, nil
}

// WriteAt implements the io.WriteAt interface.
func (w *Writer) WriteAt(p []byte, off int64) (n int, err error) {
	// cannot modify state - see io.WriteAt
	if off < 0 {
		return 0, errors.New("tdr.Writer.WriteAt: negative offset")
	}
	if off >= int64(len(w.s)) {
		return 0, io.EOF
	}
	n = copy(w.s[off:], p)
	if n < len(p) {
		err = io.EOF
	}
	return
}

// Seek sets the offset for the next Write to offset,
// interpreted according to whence:
// SeekStart means relative to the start,
// SeekCurrent means relative to the current offset, and
// SeekEnd means relative to the end.
// Seek returns the new offset relative to the start of the
// Writer and an error, if any.
func (w *Writer) Seek(offset int64, whence int) (int64, error) {
	var abs int64
	switch whence {
	case io.SeekStart:
		abs = offset
	case io.SeekCurrent:
		abs = int64(w.i) + offset
	case io.SeekEnd:
		abs = int64(len(w.s)) + offset
	default:
		return 0, errors.New("tdr.Writer.Seek: invalid whence")
	}
	if abs < 0 {
		return 0, errors.New("tdr.Writer.Seek: negative position")
	}
	w.i = int(abs)
	return abs, nil
}

// GetLeftLen return the left len for write
func (w *Writer) GetLeftLen() int {
	return len(w.s) - w.i
}

// tryGrow reslice s if possible, otherwise do grow
// It returns whether it succeeded.
func (w *Writer) tryGrow(n int) {
	needGrowLen := n - w.GetLeftLen()
	if needGrowLen <= 0 {
		return
	}

	// only reslice
	needGrowCap := needGrowLen + len(w.s) - cap(w.s)
	if needGrowCap <= 0 {
		w.s = w.s[:len(w.s)+needGrowLen]
		return
	}

	// real grow
	w.grow(needGrowCap)
}

// grow grows the buffer to guarantee space for n more bytes.
// If the buffer can't grow it will panic with ErrTooLarge.
func (w *Writer) grow(n int) {
	if w.s == nil && n <= smallBufferSize {
		w.s = make([]byte, n, smallBufferSize)
		return
	}
	c := cap(w.s)
	if c > maxInt-n {
		panic(errors.New("tdr: buffer too large"))
	} else {
		// Not enough space anywhere, we need to allocate.
		newS := make([]byte, 2*c+n)
		copy(newS, w.s)
		w.s = newS
	}
}

func NewWriter() *Writer { return &Writer{} }
