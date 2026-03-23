/**
 * Utility for safely rendering HTML content from rich-text editor.
 * Uses dangerouslySetInnerHTML only for backend-sanitized content.
 */

export function HtmlContent({ html, className = "" }) {
  if (!html || typeof html !== "string") {
    return null;
  }

  return (
    <div
      className={`html-content ${className}`.trim()}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
