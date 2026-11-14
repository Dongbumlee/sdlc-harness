# {{ProjectName}}Lib

A Java library. This README is the contract a consumer reads:
install, quickstart, supported versions, and how the API evolves.

## Install

Maven:

```xml
<dependency>
  <groupId>com.example</groupId>
  <artifactId>{{project-name}}</artifactId>
  <version>0.1.0</version>
</dependency>
```

Gradle:

```groovy
implementation 'com.example:{{project-name}}:0.1.0'
```

## Quickstart

```java
import com.example.{{PackageName}}.TextTransforms;

System.out.println(TextTransforms.slugify("Hello, World!")); // "hello-world"
System.out.println(TextTransforms.truncate("hello world", 8)); // "hello w…"
```

This example lives in `examples/Quickstart.java` and CI compiles
and runs it against the built jar, so it cannot drift from the
shipped API.

## API

The public surface is the public members of the public classes in
`com.example.{{PackageName}}`. Two mechanical checks guard it: a
reflection test pins the declared surface inside the build, and CI
diffs the compiled jar against the last release with japicmp —
binary- or source-incompatible changes fail the build.

Dependencies are declared as version ranges and there is no lock
file: a library must resolve cleanly inside the consumer's own
dependency set, not impose one.

## Supported versions

Java **21 and later** (bytecode targets release 21; CI tests JDK 21
and 25).

## Versioning and deprecation

Releases follow Semantic Versioning. Inside a major version, API
changes are additive only. Deprecation is a process, never a
surprise removal: a member is marked `@Deprecated` in one release
(the Javadoc names the replacement), stays functional, and may be
removed only in the next major version.

## Security

See [SECURITY.md](SECURITY.md) for how to report a vulnerability.

## Releases

Releases are cut from `v*.*.*` tags by
`.github/workflows/release.yml`: the tree is verified, the tag is
checked against the POM version, the built jar is smoke-tested in a
clean consumer project, the artifacts are signed and published to
Maven Central, and a GitHub Release is created from the matching
[CHANGELOG.md](CHANGELOG.md) section.

Maven Central has no trusted-publishing (OIDC) exchange, so
publishing uses a dedicated Central Portal token and a dedicated
GPG key, held as secrets on the release environment
(`MAVEN_CENTRAL_USERNAME`, `MAVEN_CENTRAL_PASSWORD`,
`GPG_PRIVATE_KEY`, `GPG_PASSPHRASE`) — the one ecosystem where the
library standard cannot go tokenless.
