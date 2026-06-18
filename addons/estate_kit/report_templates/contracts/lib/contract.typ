// EstateKit — базовый шаблон для договоров (формы)
// Юридический документ: А4, PT Sans, выключка по ширине, нумерованные разделы,
// поля для заполнения (бланки), блок реквизитов и подписей.
//
// Использование:
//   #import "../lib/contract.typ": *
//   #show: contract.with(
//     title: "ДОГОВОР № " + blank(2.5cm),
//     subtitle: "об оказании услуг по поиску потенциального Покупателя",
//     place: "г. Алматы",
//     date: dateline(),
//   )

// --- Поле для заполнения (пустой бланк): подчёркнутый промежуток заданной ширины ---
#let blank(width: 3cm) = box(
  width: width,
  stroke: (bottom: 0.6pt + black),
  outset: (bottom: 2pt),
)[#h(0pt)]

// --- Заполненное поле: значение на подчёркивании (для образцов/преднастроек) ---
#let fld(body, width: auto) = box(
  width: width,
  stroke: (bottom: 0.6pt + black),
  outset: (bottom: 2pt),
  inset: (x: 2pt),
)[#body]

// --- Поле из данных: если значение пустое (none / "") — показываем пустой бланк,
//     иначе — значение на подчёркивании. Ширина бланка для пустого значения — `width`. ---
#let fillin(value, width: 3cm) = {
  if value == none or value == "" {
    blank(width: width)
  } else {
    fld(str(value))
  }
}

// --- Строка даты в шапке договора ---
#let dateline(day: none, month: none, year: none) = {
  let d = if day != none { fld(day, width: 0.9cm) } else { box(width: 0.9cm, stroke: (bottom: 0.6pt)) }
  let m = if month != none { fld(month, width: 3cm) } else { box(width: 3cm, stroke: (bottom: 0.6pt)) }
  let y = if year != none { fld(year, width: 1.4cm) } else { box(width: 1.4cm, stroke: (bottom: 0.6pt)) }
  [«#d» #m #y г.]
}

// --- Нумерованный раздел договора (заголовок верхнего уровня) ---
#let clause(title) = heading(level: 1, title)

// --- Блок реквизитов и подписей сторон (две колонки) ---
#let requisites(left: [], right: []) = {
  v(0.5em)
  grid(
    columns: (1fr, 1fr),
    column-gutter: 1.5em,
    align: top,
    [#strong[Исполнитель] \ #left],
    [#strong[Заказчик] \ #right],
  )
}

// --- Строка подписи ---
#let sign(role: "", name: "") = {
  v(1.2em)
  grid(
    columns: (auto, 1fr, auto),
    align: (left + bottom, center + bottom, right + bottom),
    [#role], box(width: 5cm, stroke: (bottom: 0.6pt)), [#name],
  )
  v(-0.6em)
  set text(size: 8pt, fill: luma(110))
  grid(columns: (auto, 1fr, auto), [], [(подпись)], [(Ф.И.О.)])
}

// --- Основной шаблон документа ---
#let contract(
  title: none,
  subtitle: none,
  place: "г. Алматы",
  date: none,
  body,
) = {
  set document(title: if type(title) == str { title } else { "Договор" })

  set page(
    paper: "a4",
    margin: (x: 2.2cm, top: 2cm, bottom: 2cm),
    footer: context {
      set text(size: 9pt, fill: luma(120))
      align(center)[#counter(page).display("1 / 1", both: true)]
    },
  )

  set text(font: ("PT Sans", "Noto Color Emoji"), size: 11pt, lang: "ru")
  set par(justify: true, leading: 0.6em, spacing: 0.9em, first-line-indent: (amount: 1.2em, all: true))

  // Нумерованные разделы: «1. ЗАГОЛОВОК»
  set heading(numbering: "1.")
  show heading.where(level: 1): it => {
    set text(size: 11pt, weight: "bold")
    set par(first-line-indent: 0pt)
    v(0.8em)
    block(width: 100%, align(center)[#counter(heading).display() #upper(it.body)])
    v(0.3em)
  }

  // Списки/перечисления
  set enum(indent: 1em, spacing: 0.7em)
  set list(indent: 1em, marker: [—])

  // Шапка договора
  align(center)[
    #set par(first-line-indent: 0pt)
    #text(size: 14pt, weight: "bold")[#title]
    #if subtitle != none {
      v(0.2em)
      text(size: 11pt)[#subtitle]
    }
  ]
  v(0.6em)
  block[
    #set par(first-line-indent: 0pt)
    #grid(
      columns: (1fr, 1fr),
      align: (left, right),
      [#place], [#date],
    )
  ]
  v(0.4em)

  body
}
