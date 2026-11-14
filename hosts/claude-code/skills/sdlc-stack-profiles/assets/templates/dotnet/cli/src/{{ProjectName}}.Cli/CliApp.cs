using System.CommandLine;
using System.Reflection;
using {{ProjectName}}.Cli.Core;

namespace {{ProjectName}}.Cli;

/// <summary>
/// The command tree over the Cli.Core library. The command surface
/// is a contract (see the cli standard in the sdlc-stack-profiles
/// skill): data goes to stdout, diagnostics to stderr, and exit
/// codes follow the documented map — 0 success, 1 failure,
/// 2 usage error. System.CommandLine would report parse failures
/// as 1, so <see cref="Run"/> inspects the parse result first and
/// maps them to 2 itself.
/// </summary>
public static class CliApp
{
    private const string LongHelp =
        """
        {{ProjectName}} is a sample command-line tool built from the dotnet/cli
        template. It demonstrates the CLI contract: data goes to stdout,
        diagnostics go to stderr, and the command surface (flags, output
        schema, exit codes) is a tested API.

        Exit codes:
          0  success
          1  failure (the command ran but could not complete)
          2  usage error (unknown command, bad flags, invalid arguments)

        Configuration precedence: flags, then environment
        (<PREFIX>_FORMAT and friends, where the prefix is the
        upper-cased tool name), then defaults. Secrets are read from
        the environment, never from flags.
        """;

    private static readonly Option<string> FormatOption = new("--format")
    {
        Description = "Output format for data commands: plain or json.",
        Recursive = true,
    };

    private static readonly Option<bool> JsonOption = new("--json")
    {
        Description = "Shorthand for --format json.",
        Recursive = true,
    };

    private static readonly Option<bool> NoColorOption = new("--no-color")
    {
        Description = "Disable colour in diagnostics (NO_COLOR is also honoured).",
        Recursive = true,
    };

    private static readonly Option<bool> VerboseOption = new("--verbose")
    {
        Description = "Print diagnostics about what the command is doing.",
        Recursive = true,
    };

    private static readonly Option<bool> QuietOption = new("--quiet")
    {
        Description = "Suppress diagnostics.",
        Recursive = true,
    };

    private static readonly Option<bool> NoInputOption = new("--no-input")
    {
        Description = "Never prompt; fail instead of asking.",
        Recursive = true,
    };

    private static readonly Option<bool> DryRunOption = new("--dry-run")
    {
        Description = "Show what would happen without writing anything.",
        Recursive = true,
    };

    // --version is a plain recursive option handled in Run, not
    // System.CommandLine's VersionOption: the built-in reads the
    // version (and the displayed program name) from the ENTRY
    // assembly, which is this tool in production but the test host
    // in tests. Printing it here — from this assembly's own
    // informational version — keeps the shape identical everywhere.
    private static readonly Option<bool> VersionFlagOption = new("--version")
    {
        Description = "Print version.",
        Recursive = true,
    };

    /// <summary>Run the CLI over the given streams; returns the process exit code.</summary>
    public static int Run(string[] args, TextWriter stdout, TextWriter stderr)
    {
        var root = Build(stdout, stderr);
        var parseResult = root.Parse(args);
        if (parseResult.Errors.Count > 0)
        {
            foreach (var error in parseResult.Errors)
            {
                stderr.WriteLine($"error: {error.Message}");
            }

            return 2;
        }

        if (parseResult.GetValue(VersionFlagOption))
        {
            stdout.WriteLine($"{{project-name}} {VersionString()}");
            return 0;
        }

        var config = new InvocationConfiguration
        {
            Output = stdout,
            Error = stderr,
            EnableDefaultExceptionHandler = false,
        };
        try
        {
            return parseResult.Invoke(config);
        }
        catch (CliUsageException ex)
        {
            stderr.WriteLine($"error: {ex.Message}");
            return 2;
        }
        catch (CliFailureException ex)
        {
            stderr.WriteLine($"error: {ex.Message}");
            return 1;
        }
    }

    private static RootCommand Build(TextWriter stdout, TextWriter stderr)
    {
        // The root command's name comes from the assembly name
        // ({{project-name}}), which drives both usage lines and
        // the --version output shape.
        var root = new RootCommand(LongHelp);

        // Remove the VersionOption the root command carries by
        // default so the explicit VersionFlagOption above is the
        // only claimant of --version.
        foreach (var builtIn in root.Options.OfType<VersionOption>().ToList())
        {
            root.Options.Remove(builtIn);
        }
        root.Options.Add(FormatOption);
        root.Options.Add(JsonOption);
        root.Options.Add(NoColorOption);
        root.Options.Add(VerboseOption);
        root.Options.Add(QuietOption);
        root.Options.Add(NoInputOption);
        root.Options.Add(DryRunOption);
        root.Options.Add(VersionFlagOption);

        // A bare invocation (no verb) shows the help and succeeds —
        // and giving the root an action is also what lets flags like
        // --version stand alone without a "required command" parse
        // error.
        root.SetAction(parseResult =>
            root.Parse("--help").Invoke(parseResult.InvocationConfiguration));

        var text = new Command("text", "Text transformations over the Cli.Core library.");
        root.Subcommands.Add(text);
        text.Subcommands.Add(BuildSlugify(stdout, stderr));
        text.Subcommands.Add(BuildTruncate(stdout, stderr));
        return root;
    }

    /// <summary>The resolved global settings for one leaf invocation.</summary>
    private sealed record State(Output Output, bool NoInput, bool DryRun);

    private static State ResolveState(ParseResult parseResult, TextWriter stdout, TextWriter stderr)
    {
        // Configuration precedence: an explicitly passed flag wins
        // (including the --json shorthand), then the environment,
        // then the default.
        var formatResult = parseResult.GetResult(FormatOption);
        string resolved;
        if (parseResult.GetValue(JsonOption))
        {
            resolved = "json";
        }
        else if (formatResult is { Implicit: false })
        {
            resolved = parseResult.GetValue(FormatOption) ?? "plain";
        }
        else
        {
            resolved = Environment.GetEnvironmentVariable(EnvPrefix() + "FORMAT")
                ?? parseResult.GetValue(FormatOption)
                ?? "plain";
        }

        if (resolved is not ("plain" or "json"))
        {
            throw new CliUsageException($"invalid format '{resolved}': want plain or json");
        }

        var output = new Output(
            stdout,
            stderr,
            resolved,
            parseResult.GetValue(NoColorOption),
            parseResult.GetValue(QuietOption));
        return new State(output, parseResult.GetValue(NoInputOption), parseResult.GetValue(DryRunOption));
    }

    private static string EnvPrefix() => "{{project-name}}".ToUpperInvariant().Replace('-', '_') + "_";

    private static string VersionString()
    {
        var info = typeof(CliApp).Assembly
            .GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion
            ?? "0.0.0";
        var plus = info.IndexOf('+', StringComparison.Ordinal);
        return plus >= 0 ? info[..plus] : info;
    }

    private static void Deliver(
        State state,
        string result,
        IEnumerable<KeyValuePair<string, object>>? extra,
        string? outPath,
        bool force)
    {
        // Route a verb's result: stdout by default, or a file with
        // --out. File delivery honours the safety contract —
        // --dry-run writes nothing, an existing file is never
        // overwritten without --force, and the user is only ever
        // prompted at a terminal (and never with --no-input).
        if (outPath is null)
        {
            state.Output.Result(result, extra);
            return;
        }

        if (state.DryRun)
        {
            state.Output.Diagnostic($"dry-run: would write {result.Length + 1} bytes to {outPath}");
            return;
        }

        if (File.Exists(outPath) && !force)
        {
            if (state.NoInput || Console.IsInputRedirected)
            {
                throw new CliFailureException($"{outPath} already exists (use --force to overwrite)");
            }

            Console.Error.Write($"Overwrite {outPath}? [y/N] ");
            var answer = Console.ReadLine();
            if (answer is not ("y" or "Y"))
            {
                state.Output.Diagnostic($"aborted; {outPath} left unchanged");
                return;
            }
        }

        try
        {
            File.WriteAllText(outPath, result + "\n");
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
        {
            throw new CliFailureException(ex.Message);
        }

        state.Output.Diagnostic($"wrote {outPath}");
    }

    private static Command BuildSlugify(TextWriter stdout, TextWriter stderr)
    {
        var words = new Argument<string[]>("text")
        {
            Description = "The text to slugify.",
            Arity = ArgumentArity.OneOrMore,
        };
        var outOption = new Option<string?>("--out") { Description = "Write to this file." };
        var forceOption = new Option<bool>("--force") { Description = "Overwrite the --out file if it exists." };
        var command = new Command("slugify", "Convert text to a lowercase hyphenated slug.")
        {
            words,
            outOption,
            forceOption,
        };
        command.SetAction(parseResult =>
        {
            var state = ResolveState(parseResult, stdout, stderr);
            var result = TextKit.Slugify(string.Join(' ', parseResult.GetValue(words)!));
            Deliver(state, result, null, parseResult.GetValue(outOption), parseResult.GetValue(forceOption));
            return 0;
        });
        return command;
    }

    private static Command BuildTruncate(TextWriter stdout, TextWriter stderr)
    {
        var maxOption = new Option<int>("--max")
        {
            Description = "Maximum length in characters (including the ellipsis).",
            DefaultValueFactory = _ => 40,
        };
        var words = new Argument<string[]>("text")
        {
            Description = "The text to truncate.",
            Arity = ArgumentArity.OneOrMore,
        };
        var outOption = new Option<string?>("--out") { Description = "Write to this file." };
        var forceOption = new Option<bool>("--force") { Description = "Overwrite the --out file if it exists." };
        var command = new Command("truncate", "Shorten text to at most --max characters.")
        {
            maxOption,
            words,
            outOption,
            forceOption,
        };
        command.SetAction(parseResult =>
        {
            var state = ResolveState(parseResult, stdout, stderr);
            var max = parseResult.GetValue(maxOption);
            if (max < 1)
            {
                stderr.WriteLine($"error: --max must be at least 1, got {max}");
                return 2;
            }

            var source = string.Join(' ', parseResult.GetValue(words)!);
            var result = TextKit.Truncate(source, max);
            var extra = new[] { new KeyValuePair<string, object>("truncated", result != source) };
            Deliver(state, result, extra, parseResult.GetValue(outOption), parseResult.GetValue(forceOption));
            return 0;
        });
        return command;
    }
}

/// <summary>An expected, user-facing failure: message on stderr, exit 1.</summary>
internal sealed class CliFailureException(string message) : Exception(message);

/// <summary>A usage-class failure raised after parsing (a bad option value): exit 2.</summary>
internal sealed class CliUsageException(string message) : Exception(message);
