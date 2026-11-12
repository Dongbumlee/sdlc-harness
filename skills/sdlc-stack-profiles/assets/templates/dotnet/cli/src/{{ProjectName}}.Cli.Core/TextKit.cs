namespace {{ProjectName}}.Cli.Core;

/// <summary>
/// The CLI's library core: the testable logic lives here, free of
/// argument parsing and I/O, and the commands in the executable are
/// a thin shell over it.
/// </summary>
public static class TextKit
{
    /// <summary>
    /// Convert text to a lowercase, hyphen-separated slug. Letters
    /// and digits are kept, every other run of characters becomes
    /// one hyphen, and leading/trailing hyphens are trimmed.
    /// </summary>
    public static string Slugify(string text)
    {
        var slug = new System.Text.StringBuilder();
        var lastHyphen = true; // trims leading separators
        foreach (var c in text)
        {
            if (char.IsLetterOrDigit(c))
            {
                slug.Append(char.ToLowerInvariant(c));
                lastHyphen = false;
            }
            else if (!lastHyphen)
            {
                slug.Append('-');
                lastHyphen = true;
            }
        }

        return slug.ToString().TrimEnd('-');
    }

    /// <summary>
    /// Shorten text to at most <paramref name="maxLength"/>
    /// characters. An ellipsis marks truncation. A
    /// <paramref name="maxLength"/> below 1 returns an empty string.
    /// </summary>
    public static string Truncate(string text, int maxLength)
    {
        if (maxLength < 1)
        {
            return string.Empty;
        }

        if (text.Length <= maxLength)
        {
            return text;
        }

        return maxLength == 1 ? "…" : string.Concat(text.AsSpan(0, maxLength - 1), "…");
    }
}
