import { readFileSync, readdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, relative, resolve } from 'node:path'
import { defineConfig } from 'vitepress'

const root = fileURLToPath(new URL('../', import.meta.url))
const curriculum = JSON.parse(readFileSync(`${root}textbook/curriculum.json`, 'utf8'))
const appendices = readdirSync(`${root}textbook`).filter(f => f.startsWith('appendix-') && f.endsWith('.md')).sort()
const title = (file: string) => readFileSync(`${root}${file}`, 'utf8').match(/^# (.+)$/m)?.[1] ?? file
function tokenize(text: string) {
  return Array.from(new Intl.Segmenter('zh-CN', { granularity: 'word' }).segment(text))
    .filter(part => part.isWordLike).map(part => part.segment)
}

export default defineConfig({
  base: '/financial-statements/',
  lang: 'zh-CN',
  title: '读懂美国上市公司财报',
  description: '从商业交易到经营判断 · 36 章财报阅读教材',
  srcExclude: ['node_modules/**'],
  rewrites: {
    'README.md': 'project.md',
    'textbook/README.md': 'index.md',
    'textbook/:page.md': ':page.md',
    'data/README.md': 'data/index.md',
    'reviews/README.md': 'reviews/index.md'
  },
  markdown: {
    config(md) {
      // Preserve local Markdown links; only the website points to sibling Pages sites.
      md.core.ruler.after('inline', 'sibling-textbooks', state => {
        for (const block of state.tokens) {
          for (const token of block.children ?? []) {
            if (token.type !== 'link_open') continue
            const href = token.attrGet('href') ?? ''
            const match = href.match(/^\.\.\/\.\.\/(us-econ|cn-econ|mmt)\/textbook\/(.+)\.md(#.*)?$/)
            if (match) token.attrSet('href', `https://fangpings.github.io/${match[1]}/${match[2] === 'README' ? '' : match[2] + '.html'}${match[3] ?? ''}`)
            else if (/^\.\.\/data\/[^/]+\.json$/.test(href)) token.attrSet('href', '/' + href.slice(3))
            else if (/^(?![a-z]+:|\/|#).+\.md(?:#.*)?$/i.test(href)) {
              const [path, hash] = href.split('#')
              let target = relative(root, resolve(dirname(state.env.realPath ?? state.env.path), path))
              if (target === 'README.md') target = 'project.md'
              else if (target.startsWith('textbook/')) target = target.slice('textbook/'.length)
              target = target.replace(/(^|\/)README\.md$/, '$1index.md')
              token.attrSet('href', '/' + target.replace(/\.md$/, '.html') + (hash ? '#' + hash : ''))
            }
          }
        }
      })
    }
  },
  themeConfig: {
    nav: [
      { text: '学习指南', link: '/' },
      { text: '开始阅读', link: '/01-questions' },
      { text: '配套数据', link: '/data/' },
      { text: '审阅记录', link: '/reviews/' }
    ],
    sidebar: [
      { text: '学习指南与全书目录', link: '/' },
      ...curriculum.map((part: {title: string; chapters: {title: string; file: string}[]}) => ({
        text: part.title, collapsed: false,
        items: part.chapters.map(c => ({ text: c.title, link: '/' + c.file.replace(/\.md$/, '') }))
      })),
      { text: '附录', collapsed: false, items: appendices.map(file => ({ text: title(`textbook/${file}`), link: '/' + file.replace(/\.md$/, '') })) },
      { text: '配套资料', items: [{ text: '数据与复算', link: '/data/' }, { text: '审阅记录', link: '/reviews/' }] }
    ],
    outline: { level: [2, 3], label: '本页目录' },
    docFooter: { prev: '上一节', next: '下一节' },
    sidebarMenuLabel: '章节目录',
    darkModeSwitchLabel: '切换外观',
    lightModeSwitchTitle: '切换为浅色',
    darkModeSwitchTitle: '切换为深色',
    returnToTopLabel: '回到顶部',
    search: { provider: 'local', options: {
      miniSearch: { options: { tokenize } },
      translations: {
        button: { buttonText: '搜索教材', buttonAriaLabel: '搜索教材' },
        modal: { displayDetails: '显示详情', resetButtonTitle: '清除搜索', backButtonTitle: '返回', noResultsText: '没有找到相关内容', footer: { selectText: '选择', navigateText: '切换', closeText: '关闭' } }
      }
    } }
  }
})
