package jobs

import (
	"fmt"
	"strings"
	"unicode"
)

// Handlers returns the sample job types. Replace with your own;
// the contract is what matters: return the effect's result string,
// return an error wrapping ErrPermanent for payloads that can never
// succeed, and let everything else surface as retryable.
func Handlers() map[string]Handler {
	return map[string]Handler{"slugify": Slugify}
}

// Slugify turns payload["text"] into a slug — the sample job's
// effect. Lowercase, letters and digits kept, every other run of
// characters becomes one hyphen, leading/trailing hyphens trimmed —
// the same sample semantics as the other bundled templates.
func Slugify(payload map[string]any) (string, error) {
	text, _ := payload["text"].(string)
	if strings.TrimSpace(text) == "" {
		return "", fmt.Errorf("%w: payload.text must be a non-empty string", ErrPermanent)
	}
	var b strings.Builder
	lastHyphen := true // trims leading separators
	for _, r := range strings.ToLower(text) {
		switch {
		case unicode.IsLetter(r) || unicode.IsDigit(r):
			b.WriteRune(r)
			lastHyphen = false
		case !lastHyphen:
			b.WriteRune('-')
			lastHyphen = true
		}
	}
	return strings.TrimRight(b.String(), "-"), nil
}
