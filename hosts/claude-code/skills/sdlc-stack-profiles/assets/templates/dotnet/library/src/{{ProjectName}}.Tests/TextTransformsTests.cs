using Xunit;

namespace {{ProjectName}}.Tests;

/// <summary>
/// Black-box tests: they exercise the library exactly as a consumer
/// would, through its public API only. A test that reaches into
/// internals locks in the wrong contract.
/// </summary>
public class TextTransformsTests
{
    [Fact]
    public void Slugify_Lowercases_And_Hyphenates()
    {
        Assert.Equal("hello-world", TextTransforms.Slugify("Hello, World!"));
    }

    [Fact]
    public void Slugify_Folds_Accents()
    {
        Assert.Equal("deja-vu", TextTransforms.Slugify("Déjà vu"));
    }

    [Fact]
    public void Truncate_Shortens_With_Ellipsis_Counting_Toward_The_Limit()
    {
        Assert.Equal("hello w…", TextTransforms.Truncate("hello world", 8));
    }

    [Fact]
    public void Truncate_Returns_Text_That_Already_Fits_Unchanged()
    {
        Assert.Equal("short", TextTransforms.Truncate("short", 10));
    }

    [Fact]
    public void Truncate_Rejects_A_Negative_Length()
    {
        Assert.Throws<ArgumentOutOfRangeException>(
            () => TextTransforms.Truncate("abc", -1));
    }
}
