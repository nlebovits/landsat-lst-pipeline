-- Fit an included document's headings under the page title.
--
-- The About and Contribute pages include text written for another place:
-- the README partials in docs/_readme/ start at `##` or `###`, and the
-- governance files at the repository root start with a `#` title of their
-- own. The words in those files stay as they are, so this filter adjusts the
-- page around them instead:
--
-- 1. When the first block is a heading that repeats the page title, or is a
--    level-1 heading, the filter drops it. The page title already says it.
-- 2. The filter then raises every heading by the same amount, so the
--    shallowest one left is a level-2 heading under the page title.
--
-- Pages opt in with `filters: [/_headings.lua]` in their front matter.

local function normalize(text)
  return pandoc.text.lower(text):gsub("%s+", " "):gsub("^ ", ""):gsub(" $", "")
end

function Pandoc(doc)
  local title = doc.meta.title and pandoc.utils.stringify(doc.meta.title) or ""
  local blocks = doc.blocks

  -- Skip leading raw blocks, such as the `<!-- vale off -->` comments.
  local first = 1
  while blocks[first] and blocks[first].t == "RawBlock" do
    first = first + 1
  end

  local head = blocks[first]
  if head and head.t == "Header" then
    local text = pandoc.utils.stringify(head)
    if head.level == 1 or normalize(text) == normalize(title) then
      blocks:remove(first)
    end
  end

  local shallowest = math.huge
  for _, block in ipairs(blocks) do
    if block.t == "Header" and block.level < shallowest then
      shallowest = block.level
    end
  end

  if shallowest ~= math.huge and shallowest ~= 2 then
    local shift = 2 - shallowest
    doc.blocks = blocks:walk({
      Header = function(h)
        h.level = math.max(2, math.min(6, h.level + shift))
        return h
      end,
    })
  else
    doc.blocks = blocks
  end
  return doc
end
