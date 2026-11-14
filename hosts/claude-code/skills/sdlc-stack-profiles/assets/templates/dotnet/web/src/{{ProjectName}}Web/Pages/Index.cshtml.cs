using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.Extensions.Options;
using {{ProjectName}}Web.Configuration;
using {{ProjectName}}Web.Models;
using {{ProjectName}}Web.Services;

namespace {{ProjectName}}Web.Pages;

public sealed class IndexModel(ItemStore store, IOptions<PublicOptions> publicOptions) : PageModel
{
    public IReadOnlyList<Item> Items { get; private set; } = [];

    public void OnGet()
    {
        ViewData["Title"] = $"Items · {publicOptions.Value.AppName}";
        ViewData["AppName"] = publicOptions.Value.AppName;
        Items = store.List();
    }

    /// <summary>
    /// Post/redirect/get: the post answers with a redirect, so a
    /// browser refresh never resubmits the form.
    /// </summary>
    public IActionResult OnPost(string name)
    {
        if (!string.IsNullOrWhiteSpace(name))
        {
            store.Add(name.Trim());
        }

        return RedirectToPage();
    }
}
