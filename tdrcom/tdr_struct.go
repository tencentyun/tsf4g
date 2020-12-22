package tdrcom

type TDRDBFeilds struct {
	SplittableKey string
	PrimaryKey    string
	Index2Column  map[string]string
}
