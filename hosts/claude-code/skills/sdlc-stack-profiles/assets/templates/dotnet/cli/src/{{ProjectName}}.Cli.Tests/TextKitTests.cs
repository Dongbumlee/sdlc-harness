using {{ProjectName}}.Cli.Core;
using Xunit;

namespace {{ProjectName}}.Cli.Tests;

/// <summary>Unit tests for the library core, independent of the CLI shell.</summary>
public class TextKitTests
{
    [Theory]
    [InlineData("Hello, World!", "hello-world")]
    [InlineData("  spaced   out  ", "spaced-out")]
    [InlineData("CAPS LOCK", "caps-lock")]
    [InlineData("", "")]
    public void SlugifyCases(string input, string want) => Assert.Equal(want, TextKit.Slugify(input));

    [Theory]
    [InlineData("short", 40, "short")]
    [InlineData("a longer sentence", 6, "a lon…")]
    [InlineData("abc", 1, "…")]
    [InlineData("abc", 0, "")]
    public void TruncateCases(string input, int max, string want) =>
        Assert.Equal(want, TextKit.Truncate(input, max));
}
