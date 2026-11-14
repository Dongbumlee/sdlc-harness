using System.Reflection;
using Xunit;
using {{ProjectName}}API.Models;

namespace {{ProjectName}}API.Tests;

/// <summary>
/// Architecture conformance: the template's dependency direction is
/// enforced mechanically, not left to review. Endpoints may use Services
/// and Models; Services may use Models; Models use neither. A violation
/// fails the test run instead of waiting for a reviewer to notice it.
/// </summary>
public class ArchitectureTests
{
    private static readonly Assembly ApiAssembly = typeof(Item).Assembly;
    private const string Root = "{{ProjectName}}API";

    private static IEnumerable<Type> LayerTypes(string layer) =>
        ApiAssembly.GetTypes().Where(t => t.Namespace == $"{Root}.{layer}");

    private static IEnumerable<Type> ReferencedTypes(Type type)
    {
        if (type.BaseType is not null) yield return type.BaseType;
        foreach (var i in type.GetInterfaces()) yield return i;
        foreach (var f in type.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static))
            yield return f.FieldType;
        foreach (var p in type.GetProperties(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static))
            yield return p.PropertyType;
        foreach (var m in type.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly))
        {
            yield return m.ReturnType;
            foreach (var param in m.GetParameters()) yield return param.ParameterType;
        }
        foreach (var c in type.GetConstructors(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
            foreach (var param in c.GetParameters()) yield return param.ParameterType;
    }

    private static IEnumerable<Type> Unwrap(Type type)
    {
        yield return type;
        if (type.IsGenericType)
            foreach (var arg in type.GetGenericArguments())
                foreach (var t in Unwrap(arg)) yield return t;
        if (type.HasElementType && type.GetElementType() is not null)
            foreach (var t in Unwrap(type.GetElementType()!)) yield return t;
    }

    private static void AssertLayerDoesNotDependOn(string layer, params string[] forbidden)
    {
        var violations = LayerTypes(layer)
            .SelectMany(t => ReferencedTypes(t).SelectMany(Unwrap).Select(r => (From: t, To: r)))
            .Where(x => x.To.Namespace is not null && forbidden.Any(f => x.To.Namespace == $"{Root}.{f}"))
            .Select(x => $"{x.From.Name} -> {x.To.Name}")
            .Distinct()
            .ToList();
        Assert.True(violations.Count == 0,
            $"{layer} must not depend on {string.Join("/", forbidden)}: {string.Join(", ", violations)}");
    }

    [Fact]
    public void Models_depend_on_neither_services_nor_endpoints() =>
        AssertLayerDoesNotDependOn("Models", "Services", "Endpoints");

    [Fact]
    public void Services_do_not_depend_on_endpoints() =>
        AssertLayerDoesNotDependOn("Services", "Endpoints");
}
