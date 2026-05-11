// @ts-expect-error markdown-it lacks bundled types in this project
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import DOMPurify from 'dompurify'

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  highlight(code: string, language: string) {
    if (language && hljs.getLanguage(language)) {
      try {
        return hljs.highlight(code, { language, ignoreIllegals: true }).value
      } catch (_error) {
        // fall through to plain rendering
      }
    }
    return md.utils.escapeHtml(code)
  },
})

const SANITIZE_OPTIONS = {
  USE_PROFILES: { html: true },
  FORBID_TAGS: ['style', 'script', 'iframe', 'object', 'embed'],
  FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover'],
  ALLOWED_URI_REGEXP: /^(?:(?:https?|mailto|data:image\/(png|jpe?g|gif|webp);base64|\/|#)|$)/i,
}

export function renderMarkdown(input: string | null | undefined): string {
  if (!input) return ''
  const html = md.render(String(input))
  return DOMPurify.sanitize(html, SANITIZE_OPTIONS) as unknown as string
}

export function renderInlineMarkdown(input: string | null | undefined): string {
  if (!input) return ''
  const html = md.renderInline(String(input))
  return DOMPurify.sanitize(html, SANITIZE_OPTIONS) as unknown as string
}

export function truncatePlainText(input: string | null | undefined, max = 200): string {
  if (!input) return ''
  const cleaned = String(input).replace(/\s+/g, ' ').trim()
  return cleaned.length > max ? `${cleaned.slice(0, max)}…` : cleaned
}
