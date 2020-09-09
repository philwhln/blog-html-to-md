from pathlib import Path

import dateutil.parser
import html2markdown
from lxml import etree, html

HTML_DIR = Path('/Users/phil/src/philwhln/philwhln.github.io')
MARKDOWN_DIR = Path('/Users/phil/src/philwhln/blog/content/posts')


def main():
    convert_posts(HTML_DIR, MARKDOWN_DIR)


def convert_posts(html_dir, markdown_dir):
    for html_path in html_dir.glob('*.html'):
        slug = Path(html_path).stem
        if slug in ['index']:
            continue
        print('slug : ' + slug)
        convert_file(slug, html_path, markdown_dir)


def convert_file(slug, src_path, dst_dir):
    with src_path.open('rb') as f:
        html_content = f.read()

    tree = html.fromstring(html_content)
    title_raw = tree.xpath('//title/text()')[0]
    title = title_raw.replace(' | Big Fast Blog', '')
    published_raw = tree.xpath('//abbr[@class="published"]/@title')[0]
    published = dateutil.parser.parse(published_raw)
    tags = tree.xpath('//p[@class="entry-meta"]/span[@class="post_tag"]/a[@rel="tag"]/text()')
    description = tree.xpath('//head/meta[@name="description"]/@content')[0]
    try:
        post_elements = tree.xpath('//div[@class="entry-content"]/*')
    except IndexError:
        post_elements = tree.xpath('//div[@id="content"]/*')

    markdown_chunks = []
    for post_element in post_elements:
        code_elements = post_element.xpath('.//pre')
        if len(code_elements) > 0:
            for code_element in code_elements:
                etree.strip_tags(code_element, 'pre', 'span', 'del', 'small', 'strong')
                code = code_element.text
                element_markdown = '```\n' + code + '\n```'
        else:
            element_html = etree.tostring(post_element, encoding='unicode', pretty_print=True)
            element_markdown = html2markdown.convert(element_html)

        markdown_chunks.append(element_markdown)

    post_markdown = str.join('\n\n', markdown_chunks)

    dst_filename = str.join('', [
        published.strftime('%Y-%m-%d'),
        '---',
        slug,
        '.md',
    ])
    dst_path = dst_dir / dst_filename
    with dst_path.open('w') as f:
        f.write('---\n')
        f.write('title: "' + title + '"\n')
        f.write('date: "' + published.astimezone().isoformat() + '"\n')
        f.write('template: "post"\n')
        f.write('draft: false\n')
        f.write('slug: "' + slug + '"\n')
        f.write('category: "Software Engineering"\n')
        f.write('tags:\n')
        for tag in tags:
            f.write('  - ' + tag + '\n')
        f.write('description: "' + description + '"\n')
        f.write('---\n')
        f.write(post_markdown)


if __name__ == '__main__':
    main()
