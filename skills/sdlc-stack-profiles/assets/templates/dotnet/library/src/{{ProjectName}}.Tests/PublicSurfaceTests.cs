using Xunit;

namespace {{ProjectName}}.Tests;

/// <summary>
/// The public surface is the product. This test pins the set of
/// exported types so a new public type is always a deliberate act —
/// the PublicApiAnalyzers in the build pin the members the same way.
/// </summary>
public class PublicSurfaceTests
{
    [Fact]
    public void Exported_Types_Are_Exactly_The_Declared_Surface()
    {
        var exported = typeof(TextTransforms).Assembly.GetExportedTypes();

        Assert.Equal(new[] { typeof(TextTransforms) }, exported);
    }
}
