namespace {{ProjectName}}Web.Configuration;

/// <summary>
/// Application configuration, split the way the web type requires.
/// The split is structural, not a naming habit: values a browser
/// may see live in <see cref="PublicOptions"/> and are the only ones
/// a page model ever passes to a view. Server-only values live in
/// <see cref="ServerOptions"/>, are read from configuration at
/// startup, and must never be rendered, logged, or sent to a
/// client — leaking one into a page is this type's signature
/// security defect, and the test suite pins a sentinel secret out
/// of every response.
/// </summary>
public sealed class PublicOptions
{
    public const string SectionName = "Public";

    /// <summary>Browser-safe display name, rendered into pages.</summary>
    public string AppName { get; set; } = "{{ProjectName}}";
}

/// <summary>Server-only configuration: never rendered.</summary>
public sealed class ServerOptions
{
    public const string SectionName = "Server";

    /// <summary>Credential for server-side calls only.</summary>
    public string ApiKey { get; set; } = string.Empty;
}
