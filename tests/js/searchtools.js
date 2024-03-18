describe('Basic html theme search', function() {

  function loadFixture(name) {
      req = new XMLHttpRequest();
      req.open("GET", `base/tests/js/fixtures/${name}`, false);
      req.send(null);
      return req.responseText;
  }

  describe('terms search', function() {

    it('should find "C++" when in index', function() {
      eval(loadFixture("cpp/searchindex.js"));

      searchTerms = Search._parseQuery('C++');

      hits = [[
        "index",
        "&lt;no title&gt;",
        "",
        null,
        5,
        "index.rst"
      ]];
      expect(Search._performSearch(...searchTerms)).toEqual(hits);
    });

    it('should be able to search for multiple terms', function() {
      eval(loadFixture("multiterm/searchindex.js"));

      searchTerms = Search._parseQuery('main page');

      // fixme: duplicate result due to https://github.com/sphinx-doc/sphinx/issues/11961
      hits = [
        [
          'index',
          'Main Page',
          '',
          null,
          15,
          'index.rst'
        ],
        [
          'index',
          'Main Page',
          '#main-page',
          null,
          100,
          'index.rst'
        ]
      ];
      expect(Search._performSearch(...searchTerms)).toEqual(hits);
    });

  });

});

describe("htmlToText", function() {

  const testHTML = `<html>
  <body>
    <script src="directory/filename.js"></script>
    <div class="body" role="main">
      <script>
        console.log('dynamic');
      </script>
      <style>
        div.body p.centered {
          text-align: center;
          margin-top: 25px;
        }
      </style>
      <!-- main content -->
      <section id="getting-started">
        <h1>Getting Started</h1>
        <p>Some text</p>
      </section>
      <section id="other-section">
        <h1>Other Section</h1>
        <p>Other text</p>
      </section>
      <section id="yet-another-section">
        <h1>Yet Another Section</h1>
        <p>More text</p>
      </section>
    </div>
  </body>
  </html>`;

  it("basic case", () => {
    expect(Search.htmlToText(testHTML).trim().split(/\s+/)).toEqual([
      'Getting', 'Started', 'Some', 'text', 
      'Other', 'Section', 'Other', 'text', 
      'Yet', 'Another', 'Section', 'More', 'text'
    ]);
  });

  it("will start reading from the anchor", () => {
    expect(Search.htmlToText(testHTML, '#other-section').trim().split(/\s+/)).toEqual(['Other', 'Section', 'Other', 'text']);
  });
});

// This is regression test for https://github.com/sphinx-doc/sphinx/issues/3150
describe('splitQuery regression tests', () => {

  it('can split English words', () => {
    const parts = splitQuery('   Hello    World   ')
    expect(parts).toEqual(['Hello', 'World'])
  })

  it('can split special characters', () => {
    const parts = splitQuery('Pin-Code')
    expect(parts).toEqual(['Pin', 'Code'])
  })

  it('can split Chinese characters', () => {
    const parts = splitQuery('Hello from 中国 上海')
    expect(parts).toEqual(['Hello', 'from', '中国', '上海'])
  })

  it('can split Emoji (surrogate pair) characters. It should keep emojis.', () => {
    const parts = splitQuery('😁😁')
    expect(parts).toEqual(['😁😁'])
  })

  it('can split umlauts. It should keep umlauts.', () => {
    const parts = splitQuery('Löschen Prüfung Abändern ærlig spørsmål')
    expect(parts).toEqual(['Löschen', 'Prüfung', 'Abändern', 'ærlig', 'spørsmål'])
  })

})
