import { defineMarkdownComponent, type NodeTransform } from '@comark/vue';
import security from '@comark/vue/plugins/security';
import { textContent } from '@comark/vue/utils';

/**
 * The tags plain Markdown produces. An answer can quote a document or be steered by one, so any
 * other tag, raw HTML or a component name alike, is replaced by its own text: nothing in an answer
 * can run, embed a page, or make the browser fetch an image or an icon from anywhere.
 */
const ALLOWED_TAGS = [
  'p',
  'br',
  'hr',
  'strong',
  'em',
  'del',
  'code',
  'pre',
  'blockquote',
  'ul',
  'ol',
  'li',
  'a',
  'h1',
  'h2',
  'h3',
  'h4',
  'h5',
  'h6',
  'table',
  'thead',
  'tbody',
  'tr',
  'th',
  'td'
];

/**
 * Draws every code block without its header. A code fence can name a file (```` ```py [a.ext] ````),
 * and Nuxt UI's code block shows that name with an icon picked from its extension; an icon not
 * built into the page is fetched from the Iconify API, so the answer's text would choose a request
 * the browser makes. The code and its copy button stay.
 */
const hideCodeBlockHeader: NodeTransform = ({ tag, props }) =>
  tag === 'pre' ? { props: { ...props, hideHeader: true } } : undefined;

/** Renders an answer's Markdown with everything outside {@link ALLOWED_TAGS} shown as text. */
export default defineMarkdownComponent({
  name: 'AnswerMarkdown',
  // Plain Markdown only: Comark's extra syntax (raw HTML, components, attributes, autolinks) is
  // off, so raw HTML stays text and a citation such as `[2]` is not read as a component.
  registerDefaultPlugins: false,
  plugins: [
    security({
      allowedTags: ALLOWED_TAGS,
      tagFallback: element => textContent(element),
      // A link the user clicks may only leave for an https page or open a mail client.
      allowedProtocols: ['https', 'mailto'],
      allowedImagePrefixes: [],
      allowDataImages: false
    })
  ],
  transformNode: hideCodeBlockHeader,
  class: '*:first:mt-0 *:last:mb-0'
});
