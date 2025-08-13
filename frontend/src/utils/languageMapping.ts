// 语言类型映射配置

export interface LanguageInfo {
  name: string
  displayName: string
  extensions: string[]
  category: 'programming' | 'markup' | 'config' | 'data' | 'image' | 'document'
  icon?: string
  color?: string
}

// 支持的编程语言和文件类型
export const LANGUAGE_MAPPINGS: Record<string, LanguageInfo> = {
  // 编程语言
  python: {
    name: 'python',
    displayName: 'Python',
    extensions: ['.py', '.pyw', '.pyi'],
    category: 'programming',
    color: '#3776ab'
  },
  javascript: {
    name: 'javascript',
    displayName: 'JavaScript',
    extensions: ['.js', '.mjs', '.cjs'],
    category: 'programming',
    color: '#f7df1e'
  },
  typescript: {
    name: 'typescript',
    displayName: 'TypeScript',
    extensions: ['.ts', '.tsx'],
    category: 'programming',
    color: '#3178c6'
  },
  java: {
    name: 'java',
    displayName: 'Java',
    extensions: ['.java'],
    category: 'programming',
    color: '#ed8b00'
  },
  cpp: {
    name: 'cpp',
    displayName: 'C++',
    extensions: ['.cpp', '.cxx', '.cc', '.c++'],
    category: 'programming',
    color: '#00599c'
  },
  c: {
    name: 'c',
    displayName: 'C',
    extensions: ['.c'],
    category: 'programming',
    color: '#a8b9cc'
  },
  csharp: {
    name: 'csharp',
    displayName: 'C#',
    extensions: ['.cs'],
    category: 'programming',
    color: '#239120'
  },
  php: {
    name: 'php',
    displayName: 'PHP',
    extensions: ['.php', '.phtml'],
    category: 'programming',
    color: '#777bb4'
  },
  ruby: {
    name: 'ruby',
    displayName: 'Ruby',
    extensions: ['.rb', '.rbw'],
    category: 'programming',
    color: '#cc342d'
  },
  go: {
    name: 'go',
    displayName: 'Go',
    extensions: ['.go'],
    category: 'programming',
    color: '#00add8'
  },
  rust: {
    name: 'rust',
    displayName: 'Rust',
    extensions: ['.rs'],
    category: 'programming',
    color: '#dea584'
  },
  swift: {
    name: 'swift',
    displayName: 'Swift',
    extensions: ['.swift'],
    category: 'programming',
    color: '#fa7343'
  },
  kotlin: {
    name: 'kotlin',
    displayName: 'Kotlin',
    extensions: ['.kt', '.kts'],
    category: 'programming',
    color: '#7f52ff'
  },
  scala: {
    name: 'scala',
    displayName: 'Scala',
    extensions: ['.scala', '.sc'],
    category: 'programming',
    color: '#dc322f'
  },

  // 标记语言
  html: {
    name: 'html',
    displayName: 'HTML',
    extensions: ['.html', '.htm'],
    category: 'markup',
    color: '#e34f26'
  },
  css: {
    name: 'css',
    displayName: 'CSS',
    extensions: ['.css'],
    category: 'markup',
    color: '#1572b6'
  },
  scss: {
    name: 'scss',
    displayName: 'SCSS',
    extensions: ['.scss'],
    category: 'markup',
    color: '#cf649a'
  },
  sass: {
    name: 'sass',
    displayName: 'Sass',
    extensions: ['.sass'],
    category: 'markup',
    color: '#cf649a'
  },
  less: {
    name: 'less',
    displayName: 'Less',
    extensions: ['.less'],
    category: 'markup',
    color: '#1d365d'
  },
  xml: {
    name: 'xml',
    displayName: 'XML',
    extensions: ['.xml', '.xsl', '.xsd'],
    category: 'markup',
    color: '#0060ac'
  },
  markdown: {
    name: 'markdown',
    displayName: 'Markdown',
    extensions: ['.md', '.markdown'],
    category: 'markup',
    color: '#083fa1'
  },

  // 配置文件
  json: {
    name: 'json',
    displayName: 'JSON',
    extensions: ['.json'],
    category: 'config',
    color: '#292929'
  },
  yaml: {
    name: 'yaml',
    displayName: 'YAML',
    extensions: ['.yml', '.yaml'],
    category: 'config',
    color: '#cb171e'
  },
  toml: {
    name: 'toml',
    displayName: 'TOML',
    extensions: ['.toml'],
    category: 'config',
    color: '#9c4221'
  },
  ini: {
    name: 'ini',
    displayName: 'INI',
    extensions: ['.ini', '.cfg', '.conf'],
    category: 'config',
    color: '#6d6d6d'
  },

  // 数据文件
  sql: {
    name: 'sql',
    displayName: 'SQL',
    extensions: ['.sql'],
    category: 'data',
    color: '#e38c00'
  },
  csv: {
    name: 'csv',
    displayName: 'CSV',
    extensions: ['.csv'],
    category: 'data',
    color: '#217346'
  },

  // 脚本文件
  bash: {
    name: 'bash',
    displayName: 'Bash',
    extensions: ['.sh', '.bash'],
    category: 'programming',
    color: '#4eaa25'
  },
  powershell: {
    name: 'powershell',
    displayName: 'PowerShell',
    extensions: ['.ps1', '.psm1'],
    category: 'programming',
    color: '#012456'
  },
  batch: {
    name: 'batch',
    displayName: 'Batch',
    extensions: ['.bat', '.cmd'],
    category: 'programming',
    color: '#c1f12e'
  },

  // 文档文件
  text: {
    name: 'text',
    displayName: 'Text',
    extensions: ['.txt', '.log'],
    category: 'document',
    color: '#6d6d6d'
  },

  // 图片文件
  image: {
    name: 'image',
    displayName: 'Image',
    extensions: ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg'],
    category: 'image',
    color: '#ff6b6b'
  }
}

// 根据文件扩展名获取语言信息
export function getLanguageByExtension(filename: string): LanguageInfo | null {
  const extension = filename.toLowerCase().split('.').pop()
  if (!extension) return null

  const fullExtension = `.${extension}`
  
  for (const [key, language] of Object.entries(LANGUAGE_MAPPINGS)) {
    if (language.extensions.includes(fullExtension)) {
      return language
    }
  }
  
  return null
}

// 获取所有支持的语言列表
export function getAllLanguages(): LanguageInfo[] {
  return Object.values(LANGUAGE_MAPPINGS)
}

// 按类别获取语言列表
export function getLanguagesByCategory(category: LanguageInfo['category']): LanguageInfo[] {
  return Object.values(LANGUAGE_MAPPINGS).filter(lang => lang.category === category)
}

// 获取所有支持的文件扩展名
export function getSupportedExtensions(): string[] {
  const extensions = new Set<string>()
  Object.values(LANGUAGE_MAPPINGS).forEach(lang => {
    lang.extensions.forEach(ext => extensions.add(ext))
  })
  return Array.from(extensions).sort()
}

// 检查文件是否支持
export function isSupportedFile(filename: string): boolean {
  return getLanguageByExtension(filename) !== null
}

// 获取语言显示名称
export function getLanguageDisplayName(languageName: string): string {
  const language = LANGUAGE_MAPPINGS[languageName]
  return language ? language.displayName : languageName
}

// 获取语言颜色
export function getLanguageColor(languageName: string): string {
  const language = LANGUAGE_MAPPINGS[languageName]
  return language?.color || '#6d6d6d'
}
