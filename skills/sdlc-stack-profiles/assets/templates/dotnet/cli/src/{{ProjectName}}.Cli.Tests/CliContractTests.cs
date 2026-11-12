using {{ProjectName}}.Cli;
using Xunit;

namespace {{ProjectName}}.Cli.Tests;

/// <summary>
/// Contract tests for the CLI surface: golden files pin the help
/// and primary outputs, and exit-code tests pin the documented map
/// (0 success, 1 failure, 2 usage error). Regenerate goldens
/// deliberately with UPDATE_GOLDEN=1 and review the diff like an
/// API change.
/// </summary>
public class CliContractTests
{
    private static (int Exit, string Stdout, string Stderr) RunCli(params string[] args)
    {
        var stdout = new StringWriter();
        var stderr = new StringWriter();
        var exit = CliApp.Run(args, stdout, stderr);
        // System.CommandLine derives the displayed program name from
        // the ENTRY assembly: the shipped binary's name is the tool
        // name (the golden's baseline), but in-process the entry
        // assembly is the test host. Scrub it so help goldens pin
        // the surface, not the host.
        var programName = typeof(CliApp).Assembly.GetName().Name!;
        var entryName = System.Reflection.Assembly.GetEntryAssembly()?.GetName().Name;
        var output = stdout.ToString();
        if (entryName is not null && entryName != programName)
        {
            output = output.Replace(entryName, programName);
        }

        return (exit, output, stderr.ToString());
    }

    private static void Golden(string name, string actual)
    {
        var path = Path.Combine(AppContext.BaseDirectory, "TestData", name + ".golden");
        if (Environment.GetEnvironmentVariable("UPDATE_GOLDEN") == "1")
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            File.WriteAllText(path, actual);
            return;
        }

        Assert.Equal(File.ReadAllText(path), actual);
    }

    [Theory]
    [InlineData("help-root", new[] { "--help" })]
    [InlineData("help-text", new[] { "text", "--help" })]
    [InlineData("slugify", new[] { "text", "slugify", "Hello, World!" })]
    [InlineData("slugify-json", new[] { "text", "slugify", "--json", "Hello, World!" })]
    [InlineData("truncate", new[] { "text", "truncate", "--max", "6", "a longer sentence" })]
    [InlineData("truncate-json", new[] { "text", "truncate", "--max", "6", "--json", "a longer sentence" })]
    [InlineData("version", new[] { "--version" })]
    public void GoldenOutputs(string name, string[] args)
    {
        var (exit, stdout, _) = RunCli(args);
        Assert.Equal(0, exit);
        Golden(name, stdout);
    }

    [Theory]
    [InlineData(new[] { "text", "slugify", "Hello" }, 0)]
    [InlineData(new[] { "frobnicate" }, 2)]
    [InlineData(new[] { "text", "slugify" }, 2)]
    [InlineData(new[] { "text", "truncate", "--max", "abc", "text" }, 2)]
    [InlineData(new[] { "text", "truncate", "--max", "0", "text" }, 2)]
    [InlineData(new[] { "--format", "yaml", "text", "slugify", "Hi" }, 2)]
    [InlineData(new[] { "text", "slugify", "--out", "/nonexistent-dir/x.txt", "Hi" }, 1)]
    public void ExitCodes(string[] args, int want)
    {
        var (exit, _, _) = RunCli(args);
        Assert.Equal(want, exit);
    }

    [Fact]
    public void FormatPrecedence()
    {
        // Flags beat the environment, the environment beats the default.
        Environment.SetEnvironmentVariable("SAMPLE_FORMAT", "json");
        try
        {
            var (_, stdout, _) = RunCli("text", "slugify", "Hi There");
            Assert.StartsWith("{", stdout);

            var (_, plain, _) = RunCli("--format", "plain", "text", "slugify", "Hi There");
            Assert.Equal("hi-there" + Environment.NewLine, plain);
        }
        finally
        {
            Environment.SetEnvironmentVariable("SAMPLE_FORMAT", null);
        }
    }

    [Fact]
    public void FileDelivery()
    {
        // Dry-run writes nothing; overwrite needs --force.
        var dir = Directory.CreateDirectory(
            Path.Combine(Path.GetTempPath(), "{{project-name}}-cli-test-" + Guid.NewGuid().ToString("N")));
        try
        {
            var target = Path.Combine(dir.FullName, "out.txt");

            var (exit, _, _) = RunCli("text", "slugify", "--dry-run", "--out", target, "Hello World");
            Assert.Equal(0, exit);
            Assert.False(File.Exists(target), "dry-run must not write the file");

            (exit, _, _) = RunCli("text", "slugify", "--out", target, "Hello World");
            Assert.Equal(0, exit);
            Assert.Equal("hello-world\n", File.ReadAllText(target));

            (exit, _, _) = RunCli("text", "slugify", "--out", target, "Changed Text");
            Assert.Equal(1, exit);
            Assert.Equal("hello-world\n", File.ReadAllText(target));

            (exit, _, _) = RunCli("text", "slugify", "--out", target, "--force", "Changed Text");
            Assert.Equal(0, exit);
            Assert.Equal("changed-text\n", File.ReadAllText(target));
        }
        finally
        {
            dir.Delete(recursive: true);
        }
    }
}
