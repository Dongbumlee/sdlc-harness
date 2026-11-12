using System.Text.Json;

namespace {{ProjectName}}.Cli;

/// <summary>
/// The stream contract: results on stdout (plain or JSON),
/// diagnostics on stderr, and colour only where a human is looking
/// at a terminal — never in piped data.
/// </summary>
internal sealed class Output
{
    private readonly TextWriter _stdout;
    private readonly TextWriter _stderr;
    private readonly string _format;
    private readonly bool _color;
    private readonly bool _quiet;

    public Output(TextWriter stdout, TextWriter stderr, string format, bool noColor, bool quiet)
    {
        _stdout = stdout;
        _stderr = stderr;
        _format = format;
        _color = ColorEnabled(noColor);
        _quiet = quiet;
    }

    /// <summary>
    /// Print a command's primary data to stdout. In JSON mode the
    /// value is wrapped in an object with a stable <c>result</c>
    /// field; callers may add fields but the shape never changes
    /// within a major version.
    /// </summary>
    public void Result(string value, IEnumerable<KeyValuePair<string, object>>? extra = null)
    {
        if (_format == "json")
        {
            var payload = new Dictionary<string, object> { ["result"] = value };
            if (extra is not null)
            {
                foreach (var (key, fieldValue) in extra)
                {
                    payload[key] = fieldValue;
                }
            }

            _stdout.WriteLine(JsonSerializer.Serialize(payload));
        }
        else
        {
            _stdout.WriteLine(value);
        }
    }

    /// <summary>
    /// Print a human-only note to stderr, unless --quiet.
    /// Diagnostics never carry primary data.
    /// </summary>
    public void Diagnostic(string message)
    {
        if (_quiet)
        {
            return;
        }

        _stderr.WriteLine(_color ? $"\e[2m{message}\e[0m" : message);
    }

    /// <summary>
    /// Decide whether styled diagnostics are appropriate: an
    /// explicit --no-color or the NO_COLOR environment variable
    /// wins, and colour is only ever used on a terminal.
    /// </summary>
    private static bool ColorEnabled(bool noColorFlag)
    {
        if (noColorFlag)
        {
            return false;
        }

        if (Environment.GetEnvironmentVariable("NO_COLOR") is not null)
        {
            return false;
        }

        return !Console.IsErrorRedirected;
    }
}
