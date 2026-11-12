using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;

namespace {{ProjectName}}Worker.Jobs;

/// <summary>
/// Sample handlers. Replace with your own job types; the contract is what
/// matters: return the effect's result string, throw
/// <see cref="PermanentErrorException"/> for payloads that can never succeed,
/// and let everything else surface as retryable. Payloads are JSON text.
/// </summary>
public static class Handlers
{
    /// <summary>Turn payload.text into a slug — the sample job's effect.</summary>
    public static string Slugify(string payloadJson)
    {
        string? text;
        try
        {
            using var doc = JsonDocument.Parse(payloadJson);
            text = doc.RootElement.TryGetProperty("text", out var value) && value.ValueKind == JsonValueKind.String
                ? value.GetString()
                : null;
        }
        catch (JsonException)
        {
            text = null;
        }

        if (string.IsNullOrWhiteSpace(text))
        {
            throw new PermanentErrorException("payload.text must be a non-empty string");
        }

        // Lowercase, letters and digits kept, every other run of characters
        // becomes one hyphen, leading/trailing hyphens trimmed — the same
        // sample semantics as the other bundled templates.
        var slug = new StringBuilder();
        var lastHyphen = true; // trims leading separators
        foreach (var c in text.ToLowerInvariant())
        {
            if (char.IsLetterOrDigit(c))
            {
                slug.Append(c);
                lastHyphen = false;
            }
            else if (!lastHyphen)
            {
                slug.Append('-');
                lastHyphen = true;
            }
        }

        if (slug.Length > 0 && slug[^1] == '-')
        {
            slug.Length--;
        }

        return slug.ToString();
    }

    public static IReadOnlyDictionary<string, Func<string, string>> All { get; } =
        new Dictionary<string, Func<string, string>> { ["slugify"] = Slugify };
}
