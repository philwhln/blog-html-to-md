import re
from pathlib import Path

import dateutil.parser
import html2markdown
from lxml import etree, html

HTML_DIR = Path('/Users/phil/src/philwhln/philwhln.github.io')
MARKDOWN_DIR = Path('/Users/phil/src/philwhln/blog/content/posts')

CATEGORY_DEFAULT = "Software Engineering"
# This is rough bulk remapping of posts. Will do finer-grain once converted
CATEGORY_REPLACEMENTS = {
    'infrastructure': 'DevOps',
    'start-ups': 'Startups',
    'system administration': 'DevOps',
    'hadoop': 'DevOps',
    'cassandra': 'DevOps',
    'membase': 'DevOps',
    'databases': 'DevOps',
    'coding': 'Ruby',
    'uncategorized': 'old',
    'amazon': 'Startups',
    'gmail': 'Marketing',
    'imac': 'Apple',
    'apple': 'Apple',
    'battery life': 'Apple',
    'caller-id': 'Apple',
    'mobile': 'Apple',
    'bootstrapping': 'Startups',
    'aweber': 'Marketing',
    'facebook': 'Startups',
    'flash': 'Apple',
    'software development': 'Software Engineering',
    'web development': 'Software Engineering',
    'customer service': 'Startups',
    'customers': 'Startups',
    'money': 'Blogging',
}

SOCIAL_IMAGE_DEFAULT = '/images/photo.jpg'
SOCIAL_IMAGES = {
    'geohash-intro': '/wp-content/uploads/2011/08/geohash_intro_sq.jpg',
    '54-hours-in-the-okanagan-building-a-startup': '/wp-content/uploads/2012/03/office_small.jpg',
    'rollout-degrade-metrics-and-capacity': '/wp-content/uploads/2011/12/rollout-degrade-metrics-and-capacity_sq.jpg',
    'summifys-technology-examined': '/wp-content/uploads/2011/03/summify_technology_sq.jpg',
    'an-interview-with-drawn-to-scale': '/wp-content/uploads/2011/02/drawn_to_scale_sq.jpg',
    'quoras-technology-examined': '/wp-content/uploads/2011/01/quora_microscope_sq.jpg',
    'run-the-latest-whirr-and-deploy-hbase-in-minutes': '/wp-content/uploads/2011/01/whirr_hbase_sq.jpg',
    'quickly-launch-a-cassandra-cluster-on-amazon-ec2':
        '/wp-content/uploads/2011/01/launch_cassandra_amazon_ec2_sq.jpg',
    'de-volatile-your-memcached-upgrade-to-membase': '/wp-content/uploads/2011/01/memcached_to_membase_sq.jpg',
    'sqlshell-a-cross-database-sql-tool-with-nosql-potential':
        '/wp-content/uploads/2011/01/sqlshell_nosql_potential_sq.jpg',
    'hosting-images-google-storage-manager': '/wp-content/uploads/2011/01/google_storage_sq.jpg',
    'zero-copy-transfer-data-faster-in-ruby': '/wp-content/uploads/2011/01/zero_copy_ruby_sq.jpg',
    'the-apache-projects-the-justice-league-of-scalability': '/wp-content/uploads/2011/01/apache_justice_league_sq.jpg',
    'landsliding-into-postgis-with-kml-files': '/wp-content/uploads/2011/01/postgis_kml_sq.jpg',
    'embed-base64-encoded-images-inline-in-html': '/wp-content/uploads/2011/01/html_inline_image_sq.jpg',
    'map-reduce-with-ruby-using-hadoop': '/wp-content/uploads/2010/12/hadoop_ruby_sq.jpg',
    'homebrew-intro-to-the-mac-os-x-package-installer': '/wp-content/uploads/2010/12/homebrew_intro_sq.jpg',
    'how-to-get-experience-working-with-large-datasets': '/wp-content/uploads/2010/12/big_dataset_experience_sq.jpg',
    'find-the-road-to-your-happiness-by-helping-others': '/wp-content/uploads/2010/12/help_others_sq.jpg',
}

CODE_LANGUAGE_KEYWORDS = {
    'ruby': [
        'ApplicationController',
        'Rails::Application',
        'SystemExit',
        'at_exit',
        'eventmachine',
        'get_current_user',
    ],
    # don't format bash/sh code. doesn't work well
    '': [
        'gem install',
        'phil@air:',
        'root@localhost:',
        'ruby -e',
    ],
}


def main():
    convert_posts(HTML_DIR, MARKDOWN_DIR)


def convert_posts(html_dir, markdown_dir):
    for html_path in html_dir.glob('*.html'):
        slug = Path(html_path).stem
        if slug in ['index']:
            continue
        print('slug : ' + slug)
        convert_file(slug, html_path, markdown_dir)


def _choose_category(categories):
    if len(categories) == 0:
        return CATEGORY_DEFAULT
    category = categories[0]
    lookup = str.lower(category)
    if lookup in CATEGORY_REPLACEMENTS:
        return CATEGORY_REPLACEMENTS[lookup]
    return category


def convert_file(slug, src_path, dst_dir):
    with src_path.open('rb') as f:
        html_content = f.read()

    tree = html.fromstring(html_content)
    title_raw = tree.xpath('//title/text()')[0]
    title = title_raw.replace('"', '').replace(' | Big Fast Blog', '')
    published_raw = tree.xpath('//abbr[@class="published"]/@title')[0]
    published = dateutil.parser.parse(published_raw)
    tags = tree.xpath('//p[@class="entry-meta"]/span[@class="post_tag"]/a[@rel="tag"]/text()')
    categories = tree.xpath('//p[@class="entry-meta"]/span[@class="category"]/a[@rel="tag"]/text()')
    category = _choose_category(categories)
    description_raw = tree.xpath('//head/meta[@name="description"]/@content')[0]
    description = description_raw.replace('"', '')

    if slug in SOCIAL_IMAGES:
        social_image = SOCIAL_IMAGES[slug]
    else:
        social_image = SOCIAL_IMAGE_DEFAULT

    try:
        post_elements = tree.xpath('//div[@class="entry-content"]/*')
    except IndexError:
        post_elements = tree.xpath('//div[@id="content"]/*')

    markdown_chunks = []
    for post_element in post_elements:
        code_elements = post_element.xpath('.//pre')
        if len(code_elements) == 0 and post_element.tag == 'pre':
            code_elements = [post_element]
        markdown_chunk = None
        if len(code_elements) > 0:
            codeblock_language = ''
            for code_element in code_elements:
                etree.strip_tags(code_element, 'del', 'em', 'pre', 'small', 'span', 'strong')
                code = code_element.text
                for language, code_keywords in CODE_LANGUAGE_KEYWORDS.items():
                    for keyword in code_keywords:
                        if keyword in code:
                            codeblock_language = language
                markdown_chunk = '```' + codeblock_language + '\n' + code + '\n```'
        else:
            html_chunk = etree.tostring(post_element, encoding='unicode', pretty_print=True)
            markdown_chunk = html2markdown.convert(html_chunk)

        markdown_chunks.append(markdown_chunk)

    post_markdown = str.join('\n\n', markdown_chunks)

    comments_elements = tree.xpath('//div[@id="comments"]')
    comments_html = None
    if len(comments_elements) > 0:
        comments_element = comments_elements[0]
        # remove links (with <a>) and formatted (with <span>)
        etree.strip_tags(comments_element, 'a', 'span')
        etree.indent(comments_element, space="  ")
        comments_html_raw = etree.tostring(comments_element, encoding='unicode', pretty_print=True)
        comments_html = re.sub('\n\n+', '\n', comments_html_raw).strip()

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
        f.write('category: "' + category + '"\n')
        if len(tags) == 0:
            f.write('tags: []\n')
        else:
            f.write('tags:\n')
            for tag in tags:
                f.write('  - ' + tag + '\n')
        f.write('description: "' + description + '"\n')
        f.write('socialImage:\n')
        f.write('  publicURL: "' + social_image + '"\n')
        f.write('---\n')
        f.write(post_markdown)
        f.write('\n\n')
        if comments_html:
            f.write(comments_html)
            f.write('\n\n')


if __name__ == '__main__':
    main()
