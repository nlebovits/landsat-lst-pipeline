-- Remove a level-1 heading whose text equals the page title.
--
-- The homepage includes docs/_readme/intro.md, which opens with the README's
-- `#` title. The page uses the same words as its title, then a summary, then
-- the rest of the partial. Without this filter the title would print twice.
-- The partial's words stay as they are.

function Pandoc(doc)
  local title = doc.meta.title and pandoc.utils.stringify(doc.meta.title) or ""
  doc.blocks = doc.blocks:filter(function(block)
    return not (block.t == "Header" and block.level == 1
      and pandoc.utils.stringify(block) == title)
  end)
  return doc
end
