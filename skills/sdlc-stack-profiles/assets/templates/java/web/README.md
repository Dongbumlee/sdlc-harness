# {{project-name}} web

A server-rendered web app built from the java/web template
(Spring Boot + Thymeleaf). The sample slice (an items page with
an add form) is a placeholder — replace it with your own pages;
the delivery guarantees around it are the template.

## The web contract

The browser is untrusted, and the template is shaped by that:

- **Environment split, structurally.** Configuration comes in
  two `@ConfigurationProperties` records (`config` package):
  `PublicProperties` (`app.public.*`) — browser-safe values that
  controllers may put in the model — and `ServerProperties`
  (`app.server.*`) — secrets that must never be rendered,
  logged, or sent to a client. Leaking a server secret into a
  page is this type's signature security defect; `SecretLeakTest`
  pins a sentinel secret out of every response while asserting
  the public values do render. Binding follows Spring Boot's
  relaxed rules, so `app.public.app-name` binds from the
  environment variable `APP_PUBLIC_APPNAME` and
  `app.server.api-key` from `APP_SERVER_APIKEY`.
- **Markup floor (WCAG 2.2 AA).** The shared Thymeleaf layout
  ships with a language attribute, a skip link, landmark
  regions, and visible focus; each page carries exactly one
  `<h1>` and labelled form controls. The page tests assert the
  floor so a new page cannot silently drop it.
- **Post/redirect/get.** Form posts answer with a redirect, so
  a refresh never resubmits.
- **Server-rendered first.** Pages render on the server with
  Thymeleaf (expressions escaped by default); client scripts
  enhance, they are not the only path to the content.

## Tests

`WebPageTest` drives the app through MockMvc: the items page
renders the sample slice, the markup floor holds, the add-item
journey completes, static assets are served, and `/health`
answers. `ArchitectureTest` enforces the layer direction
mechanically (web → service/config/model; service → model;
config and model depend on nothing internal), and
`SecretLeakTest` carries the leak guarantee described above.

## Running

```bash
./mvnw spring-boot:run
```

The app listens on port 8080.

## Development

```bash
./mvnw test
```
