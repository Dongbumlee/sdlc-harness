// The `go` directive is the library's support floor: consumers on this
// Go version or newer can build the module, and CI tests the floor and
// the current release. Raise it only in a major release.
module example.com/{{project-name}}

go 1.26
