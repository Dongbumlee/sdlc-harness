// Thin entry point: everything testable lives in CliApp and the
// Cli.Core library; Main only wires the real console streams.
return {{ProjectName}}.Cli.CliApp.Run(args, Console.Out, Console.Error);
