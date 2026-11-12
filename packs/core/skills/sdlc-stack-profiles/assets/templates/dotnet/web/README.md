# {{project-name}} web

A server-rendered web app built from the dotnet/web template
(ASP.NET Core Razor Pages). The sample slice (an items page with
an add form) is a placeholder — replace it with your own pages;
the delivery guarantees around it are the template.

## The web contract

The browser is untrusted, and the template is shaped by that:

- **Environment split, structurally.** Configuration comes in
  two option classes bound from two configuration sections
  (`Configuration/AppOptions.cs`): `PublicOptions` — browser-safe
  values that page models may pass to views — and
  `ServerOptions` — secrets that must never be rendered, logged,
  or sent to a client. Leaking a server secret into a page is
  this type's signature security defect; the test suite pins a
  sentinel secret out of every response while asserting the
  public values do render.
- **Markup floor (WCAG 2.2 AA).** The shared layout ships with a
  language attribute, a skip link, landmark regions, and visible
  focus; each page carries exactly one `<h1>` and labelled form
  controls. The page tests assert the floor so a new page cannot
  silently drop it.
- **Post/redirect/get, antiforgery on.** Form posts answer with
  a redirect, so a refresh never resubmits; Razor Pages'
  antiforgery validation stays enabled, and the journey test
  exercises it the way a browser would (token + cookie).
- **Server-rendered first.** Pages render on the server from the
  same service layer an API would use; client scripts enhance,
  they are not the only path to the content.

## Tests

`WebPageTests` drives the app over HTTP with
`WebApplicationFactory`: the items page renders the sample
slice, the markup floor holds, the add-item journey completes,
static assets are served, `/health` answers, and the
secret-leak test described above passes. `ArchitectureTests`
enforces the layer direction mechanically.

## Running

```bash
dotnet run --project src/{{ProjectName}}Web
```

Configuration sections `Public` and `Server` come from
appsettings or the environment (`Public__AppName`,
`Server__ApiKey`).

## Development

```bash
dotnet test {{ProjectName}}.sln
dotnet format {{ProjectName}}.sln --verify-no-changes
```
