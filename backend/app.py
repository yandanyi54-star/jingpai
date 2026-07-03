from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import markdown
from bs4 import BeautifulSoup
import os 

app = Flask(__name__)
CORS(app)
UNSPLASH_ACCESS_KEY = "mB4xGGyf3N0NF7an4W3F1e5uNUw_6Uw46LIiwVJcpD8"

# ---------- 预设主题配置 ----------
THEMES = {
    "serif_news": {
        "name": "📰 经典报业",
        "styles": {
            "h1": {"font-size": "32px", "font-weight": "bold", "text-align": "center", "color": "#8b0000", "font-family": "Georgia, 'Times New Roman', serif", "margin": "20px 0 12px"},
            "h2": {"font-size": "22px", "font-weight": "bold", "color": "#222", "font-family": "Georgia, 'Times New Roman', serif", "border-bottom": "2px solid #ccc", "padding-bottom": "6px", "margin": "18px 0 10px"},
            "h3": {"font-size": "19px", "font-weight": "bold", "color": "#333", "font-family": "Georgia, 'Times New Roman', serif"},
            "p": {"font-size": "17px", "line-height": "1.9", "color": "#333", "font-family": "Georgia, 'Times New Roman', serif", "text-indent": "2em", "margin": "0 0 16px 0"},
            "blockquote": {"border-left": "4px solid #8b0000", "padding-left": "16px", "color": "#555", "font-family": "Georgia, 'Times New Roman', serif", "margin": "16px 0"},
            "code": {"background": "#f4f4f4", "padding": "2px 6px", "border-radius": "4px", "font-family": "monospace"}
        }
    },
    "neon_tech": {
        "name": "💻 霓虹赛博",
        "styles": {
            "h1": {"font-size": "30px", "font-weight": "900", "color": "#00ff41", "background": "#0a0a0a", "padding": "12px", "text-align": "center", "font-family": "'Courier New', monospace", "border-radius": "8px"},
            "h2": {"font-size": "24px", "font-weight": "bold", "color": "#00ff41", "border-left": "6px solid #00ff41", "padding-left": "14px", "font-family": "'Courier New', monospace", "margin": "20px 0 12px"},
            "h3": {"font-size": "18px", "font-weight": "bold", "color": "#ff00ff", "font-family": "'Courier New', monospace"},
            "p": {"font-size": "16px", "line-height": "1.8", "color": "#d3d3d3", "background": "#1a1a1a", "padding": "10px 14px", "font-family": "'Courier New', monospace", "margin": "0 0 12px 0", "border-radius": "4px"},
            "blockquote": {"border-left": "4px solid #ff00ff", "padding-left": "16px", "color": "#ff00ff", "background": "#2a0a2a", "font-family": "'Courier New', monospace", "padding": "12px", "border-radius": "4px"},
            "code": {"background": "#2d2d2d", "color": "#f8f8f2", "padding": "2px 8px", "border-radius": "4px"}
        }
    },
    "mellow_pink": {
        "name": "🌸 温柔奶油",
        "styles": {
            "h1": {"font-size": "28px", "font-weight": "600", "color": "#b34180", "text-align": "center", "font-family": "'PingFang SC', 'Microsoft YaHei', sans-serif", "background": "#fce4ec", "border-radius": "30px", "padding": "12px 20px", "display": "inline-block"},
            "h2": {"font-size": "22px", "font-weight": "600", "color": "#b34180", "border-bottom": "3px solid #f8bbd0", "padding-bottom": "8px", "font-family": "'PingFang SC', 'Microsoft YaHei', sans-serif"},
            "h3": {"font-size": "19px", "font-weight": "500", "color": "#8d6e63", "font-family": "'PingFang SC', 'Microsoft YaHei', sans-serif"},
            "p": {"font-size": "17px", "line-height": "2", "color": "#5d4037", "font-family": "'PingFang SC', 'Microsoft YaHei', sans-serif", "background": "#fff9f9", "padding": "6px 16px", "border-radius": "12px", "margin": "0 0 14px 0"},
            "blockquote": {"border-left": "4px solid #f06292", "padding-left": "16px", "color": "#880e4f", "background": "#fce4ec", "border-radius": "8px", "padding": "12px 16px"},
            "code": {"background": "#f3e5f5", "color": "#6a1b9a", "padding": "2px 8px", "border-radius": "12px"}
        }
    },
    "zen_minimal": {
        "name": "🍃 禅意极简",
        "styles": {
            "h1": {"font-size": "36px", "font-weight": "300", "color": "#2c3e50", "text-align": "center", "font-family": "'Times New Roman', serif", "letter-spacing": "6px", "margin": "20px 0 16px"},
            "h2": {"font-size": "20px", "font-weight": "300", "color": "#7f8c8d", "text-align": "center", "font-family": "'Times New Roman', serif", "border-top": "1px solid #ecf0f1", "padding-top": "14px", "letter-spacing": "2px"},
            "h3": {"font-size": "17px", "font-weight": "400", "color": "#34495e", "font-family": "'Times New Roman', serif"},
            "p": {"font-size": "18px", "line-height": "2.6", "color": "#2c3e50", "font-family": "'Times New Roman', serif", "letter-spacing": "0.5px", "margin": "0 0 20px 0"},
            "blockquote": {"border-left": "4px solid #bdc3c7", "padding-left": "20px", "color": "#95a5a6", "font-family": "'Times New Roman', serif", "font-style": "italic"},
            "code": {"background": "#f8f9fa", "padding": "2px 8px", "border-radius": "2px", "color": "#e74c3c"}
        }
    }
}

# ---------- 核心转换函数 ----------
def apply_inline_styles(html_content, theme_styles):
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in soup.find_all():
        tag_name = tag.name
        if tag_name in theme_styles:
            style_dict = theme_styles[tag_name]
            style_str = "; ".join([f"{k}: {v}" for k, v in style_dict.items()])
            if tag.has_attr('style'):
                tag['style'] = tag['style'] + "; " + style_str
            else:
                tag['style'] = style_str
    return str(soup)

# ---------- API 路由 ----------
@app.route('/convert', methods=['POST'])
def convert_markdown():
    data = request.get_json()
    md_text = data.get('markdown', '')
    theme_id = data.get('theme', 'podcast')
    
    raw_html = markdown.markdown(md_text, extensions=['extra'])
    theme_config = THEMES.get(theme_id, THEMES.get('serif_news', list(THEMES.values())[0]))
    styled_html = apply_inline_styles(raw_html, theme_config['styles'])
    
    return jsonify({
        'success': True,
        'html': styled_html,
        'theme_name': theme_config['name']
    })
# ---------- Unsplash 代理 API ----------
@app.route('/unsplash/search', methods=['GET'])
def search_unsplash():
    query = request.args.get('query', '')
    if not query:
        return jsonify({'error': '请提供搜索关键词'}), 400
    
    # 设置请求头和参数
    headers = {
        'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'
    }
    params = {
        'query': query,
        'per_page': 9,  # 一次返回9张图片
        'orientation': 'landscape'  # 偏好横图
    }
    
    try:
        # 调用 Unsplash API
        response = requests.get(
            'https://api.unsplash.com/search/photos',
            headers=headers,
            params=params
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'Unsplash API 请求失败'}), response.status_code
        
        data = response.json()
        # 提取我们需要的图片信息
        results = []
        for photo in data.get('results', []):
            results.append({
                'id': photo['id'],
                'thumb': photo['urls']['thumb'],  # 缩略图，用于展示
                'regular': photo['urls']['regular'],  # 大图，用于插入
                'alt': photo.get('alt_description', '') or photo.get('description', ''),
                'author': photo['user']['name']
            })
        
        return jsonify({'results': results})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# ---------- 托管前端静态文件 ----------
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    dist_dir = os.path.join(os.path.dirname(__file__), '../frontend/dist')
    if path == '' or not os.path.exists(os.path.join(dist_dir, path)):
        return send_from_directory(dist_dir, 'index.html')
    return send_from_directory(dist_dir, path)

# ---------- 启动 ----------
if __name__ == '__main__':
    app.run(debug=True, port=5000)