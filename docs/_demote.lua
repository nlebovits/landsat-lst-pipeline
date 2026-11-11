-- Lower every heading inside a `.demote` div by one level.
--
-- The landing page includes docs/_readme/intro.md, which opens with the
-- README's own `#` title. The page already has a hero `#` heading, so the
-- included title would be a second level-1 heading. The words of the partial
-- stay as they are, so this filter changes the level around them instead.
-- docs/_headings.lua cannot do this job: it drops a page's first level-1
-- heading, which on the landing page is the hero.
--
-- Pages opt in with `filters: [/_demote.lua]` and wrap the include:
--
--     ::: demote
--     {{< include /_readme/intro.md >}}
--     :::

function Div(div)
  if not div.classes:includes("demote") then
    return nil
  end
  return div:walk({
    Header = function(h)
      h.level = math.min(6, h.level + 1)
      return h
    end,
  })
end
