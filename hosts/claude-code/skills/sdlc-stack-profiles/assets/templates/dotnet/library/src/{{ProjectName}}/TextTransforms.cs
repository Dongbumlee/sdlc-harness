using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace {{ProjectName}};

/// <summary>
/// Text helpers published by {{ProjectName}}. This class is the
/// library's public surface in miniature: everything a consumer may
/// rely on is public and declared in PublicAPI.Unshipped.txt;
/// anything else is internal and may change without notice.
/// </summary>
public static partial class TextTransforms
{
    /// <summary>
    /// Returns a URL-safe slug for <paramref name="text"/>: accents
    /// are folded to their ASCII base letters and every run of
    /// remaining non-alphanumeric characters becomes one hyphen.
    /// </summary>
    public static string Slugify(string text)
    {
        ArgumentNullException.ThrowIfNull(text);
        var folded = FoldToAscii(text.Trim().ToLowerInvariant());
        return NonSlugChars().Replace(folded, "-").Trim('-');
    }

    /// <summary>
    /// Shortens <paramref name="text"/> to at most
    /// <paramref name="maxLength"/> characters, ending with
    /// <paramref name="ellipsis"/> (which counts toward the limit).
    /// Text that already fits is returned unchanged.
    /// </summary>
    public static string Truncate(string text, int maxLength, string ellipsis = "…")
    {
        ArgumentNullException.ThrowIfNull(text);
        ArgumentOutOfRangeException.ThrowIfNegative(maxLength);
        if (text.Length <= maxLength)
        {
            return text;
        }

        if (maxLength <= ellipsis.Length)
        {
            return ellipsis[..maxLength];
        }

        return string.Concat(text.AsSpan(0, maxLength - ellipsis.Length), ellipsis);
    }

    private static string FoldToAscii(string text)
    {
        var builder = new StringBuilder(text.Length);
        foreach (var ch in text.Normalize(NormalizationForm.FormD))
        {
            if (CharUnicodeInfo.GetUnicodeCategory(ch) != UnicodeCategory.NonSpacingMark)
            {
                builder.Append(ch);
            }
        }

        return builder.ToString();
    }

    [GeneratedRegex("[^a-z0-9]+")]
    private static partial Regex NonSlugChars();
}
