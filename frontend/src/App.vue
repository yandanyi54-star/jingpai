<template>
  <div id="app">
    <!-- 顶部工具栏 -->
    <header class="toolbar">
      <h1>🎙️ PodcastPublish</h1>
      <div class="toolbar-actions">
        <select v-model="currentTheme" @change="onThemeChange">
          <option value="serif_news">📰 经典报业</option>
          <option value="neon_tech">💻 霓虹赛博</option>
          <option value="mellow_pink">🌸 温柔奶油</option>
          <option value="zen_minimal">🍃 禅意极简</option>
        </select>
        <button @click="showPanel = !showPanel" class="btn-style">🎨 调节样式</button>
        <button @click="showImagePanel = !showImagePanel" class="btn-image">🖼️ 配图推荐</button>
        <button @click="copyHtml" class="btn-copy">📋 复制 HTML</button>
      </div>
    </header>
        <!-- 样式调节面板 -->
    <div v-if="showPanel" class="style-panel">
      <div class="style-controls">
        <label>选择标签：</label>
        <select v-model="selectedTag">
          <option value="h1">H1 标题</option>
          <option value="h2">H2 标题</option>
          <option value="h3">H3 标题</option>
          <option value="p">正文段落</option>
          <option value="blockquote">引用块</option>
        </select>
        <label>字号 (px)：</label>
        <input type="number" v-model.number="tempFontSize" min="12" max="48" @input="applyCustomStyle" />
        <label>颜色：</label>
        <input type="color" v-model="tempColor" @input="applyCustomStyle" />
        <button @click="resetTagStyle" class="btn-reset">重置该标签</button>
      </div>
    </div>

    <!-- 配图推荐面板 -->
    <div v-if="showImagePanel" class="image-panel">
      <div class="image-controls">
        <input type="text" v-model="searchQuery" placeholder="输入关键词搜索图片..." @keyup.enter="searchImages" />
        <button @click="searchImages" class="btn-search">搜索</button>
        <span v-if="imageLoading" class="status-text">加载中...</span>
        <span v-if="imageError" class="status-text error">{{ imageError }}</span>
      </div>
      <div v-if="imageResults.length > 0" class="image-grid">
        <div v-for="img in imageResults" :key="img.id" class="image-item" @click="insertImage(img.regular, img.alt)">
          <img :src="img.thumb" :alt="img.alt" />
          <div class="image-author">📸 {{ img.author }}</div>
        </div>
      </div>
    </div>

    <!-- 主体 -->
    <main class="main-layout">
      <!-- 左：编辑器 -->
      <section class="editor-panel">
        <MdEditor v-model="markdownText" language="zh-CN" />
      </section>

      <!-- 右：手机预览 -->
      <section class="preview-panel">
        <div class="phone-frame">
          <div class="phone-content" v-html="previewHtml"></div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import { MdEditor } from 'md-editor-v3';
import 'md-editor-v3/lib/style.css';
import axios from 'axios';
import DOMPurify from 'dompurify';

// ---------- UI 控制 ----------
const showPanel = ref(false);
const showImagePanel = ref(false);

// ---------- 配图功能 ----------
const searchQuery = ref('');
const imageResults = ref([]);
const imageLoading = ref(false);
const imageError = ref('');

// ---------- 编辑器内容 ----------
const markdownText = ref('# 欢迎使用 PodcastPublish\n\n这是你的第一篇播客精华。\n## 亮点\n- 支持 Markdown 语法\n- 右侧实时预览公众号风格\n- 点击复制即可粘贴到微信后台');
const previewHtml = ref('');
const currentTheme = ref('serif_news');

// ---------- 样式调节 ----------
const selectedTag = ref('h2');
const tempFontSize = ref(22);
const tempColor = ref('#07c160');
const customOverrides = ref({});

// ---------- 加载本地存储 ----------
const loadFromStorage = () => {
  const saved = localStorage.getItem('podcast_theme_overrides');
  if (saved) {
    try {
      customOverrides.value = JSON.parse(saved);
    } catch (e) {
      customOverrides.value = {};
    }
  }
};

// ---------- 保存到本地存储 ----------
const saveToStorage = () => {
  localStorage.setItem('podcast_theme_overrides', JSON.stringify(customOverrides.value));
};

// ---------- 核心转换 ----------
const convertMarkdown = async () => {
  try {
    const response = await axios.post('http://localhost:5000/convert', {
      markdown: markdownText.value,
      theme: currentTheme.value,
      overrides: customOverrides.value
    });
    previewHtml.value = DOMPurify.sanitize(response.data.html);
  } catch (error) {
    console.error('转换失败:', error);
    previewHtml.value = '<p style="color:red;">⚠️ 后端连接失败，请确保已运行 python app.py</p>';
  }
};

// ---------- 应用自定义样式 ----------
const applyCustomStyle = () => {
  if (!selectedTag.value) return;
  const newStyle = {};
  if (tempFontSize.value) newStyle['font-size'] = tempFontSize.value + 'px';
  if (tempColor.value) newStyle['color'] = tempColor.value;
  
  if (!customOverrides.value[selectedTag.value]) {
    customOverrides.value[selectedTag.value] = {};
  }
  Object.assign(customOverrides.value[selectedTag.value], newStyle);
  
  if (Object.keys(customOverrides.value[selectedTag.value]).length === 0) {
    delete customOverrides.value[selectedTag.value];
  }
  
  saveToStorage();
  convertMarkdown();
};

// ---------- 重置单个标签 ----------
const resetTagStyle = () => {
  if (selectedTag.value) {
    delete customOverrides.value[selectedTag.value];
    saveToStorage();
    convertMarkdown();
    tempFontSize.value = '';
    tempColor.value = '#000000';
  }
};

// ---------- 配图功能 ----------
const searchImages = async () => {
  if (!searchQuery.value.trim()) {
    imageError.value = '请输入搜索关键词';
    return;
  }
  
  imageLoading.value = true;
  imageError.value = '';
  imageResults.value = [];
  
  try {
    const response = await axios.get('http://localhost:5000/unsplash/search', {
      params: { query: searchQuery.value }
    });
    
    if (response.data.error) {
      imageError.value = response.data.error;
    } else {
      imageResults.value = response.data.results;
      if (imageResults.value.length === 0) {
        imageError.value = '未找到相关图片，试试其他关键词';
      }
    }
  } catch (error) {
    console.error('搜索图片失败:', error);
    imageError.value = '图片搜索失败，请稍后重试';
  } finally {
    imageLoading.value = false;
  }
};

// ---------- 插入图片到编辑器 ----------
const insertImage = (url, alt) => {
  const imageMarkdown = `\n![${alt || '图片'}](${url})\n`;
  markdownText.value = markdownText.value + imageMarkdown;
};

// ---------- 复制 HTML ----------
const copyHtml = async () => {
  const htmlToCopy = previewHtml.value;
  if (!htmlToCopy) return alert('没有内容可复制');
  try {
    const blob = new Blob([htmlToCopy], { type: 'text/html' });
    const clipboardItem = new ClipboardItem({
      'text/html': blob
    });
    await navigator.clipboard.write([clipboardItem]);
    alert('✅ 已复制！直接粘贴到微信公众号后台即可。');
  } catch (err) {
    alert('复制失败，请手动选择右侧预览区内容，按 Ctrl+C 复制');
    console.error(err);
  }
};

// ---------- 主题切换 ----------
const onThemeChange = () => {
  convertMarkdown();
};

// ---------- 监听编辑器内容变化 ----------
watch(markdownText, () => {
  convertMarkdown();
});

// ---------- 初始化 ----------
onMounted(() => {
  loadFromStorage();
  if (customOverrides.value['h2']) {
    const h2 = customOverrides.value['h2'];
    if (h2['font-size']) tempFontSize.value = parseInt(h2['font-size']);
    if (h2['color']) tempColor.value = h2['color'];
  }
  convertMarkdown();
});
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
#app {
  height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background: #f5f5f5;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: white;
  border-bottom: 1px solid #e8e8e8;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  z-index: 10;
}
.toolbar h1 {
  font-size: 20px;
  color: #1a1a1a;
}
.toolbar-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}
.toolbar-actions select {
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid #ddd;
  background: white;
  font-size: 14px;
  cursor: pointer;
}
.btn-copy {
  padding: 6px 18px;
  background: #07c160;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-copy:hover {
  background: #06ad56;
}
.main-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
  gap: 0;
}
.editor-panel {
  flex: 1;
  height: 100%;
  background: white;
  border-right: 1px solid #e8e8e8;
  overflow: hidden;
}
.editor-panel :deep(.md-editor) {
  height: 100% !important;
}
.preview-panel {
  flex: 1;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f0f0f0;
  padding: 20px;
}
.phone-frame {
  width: 375px;
  height: 100%;
  max-height: 780px;
  background: white;
  border-radius: 28px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.12);
  overflow: hidden;
  padding: 20px 16px;
  position: relative;
}
.phone-content {
  height: 100%;
  overflow-y: auto;
  font-size: 17px;
  line-height: 1.8;
  color: #3e3e3e;
  padding-right: 4px;
}
.phone-content::-webkit-scrollbar {
  width: 4px;
}
.phone-content::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 4px;
}
</style>