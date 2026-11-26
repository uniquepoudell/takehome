/* Take-home pay calculator. Same maths as tax.py (tests compare them). */
(function (root) {
  "use strict";
  function bracketTax(income, brackets) {
    var tax = 0, lower = 0;
    for (var i = 0; i < brackets.length; i++) {
      var upper = brackets[i][0], rate = brackets[i][1];
      var top = upper === null ? income : Math.min(income, upper);
      if (top > lower) tax += (top - lower) * rate;
      if (upper === null || income <= upper) break;
      lower = upper;
    }
    return tax;
  }
  function lito(R, x) {
    var p = R.lito;
    if (x <= p.full_to) return p.max;
    if (x <= p.mid_to) return p.max - (x - p.full_to) * 0.05;
    if (x <= p.zero_at) return Math.max(0, p.mid_value - (x - p.mid_to) * 0.015);
    return 0;
  }
  function medicare(R, x) {
    var m = R.medicare;
    if (x <= m.low) return 0;
    return Math.min(x * m.rate, (x - m.low) * 0.10);
  }
  function helpRepay(R, x) {
    var h = R.help;
    if (x <= h.threshold) return 0;
    if (x <= h.band2) return (x - h.threshold) * h.rate1;
    if (x < h.top) return h.band2_base + (x - h.band2) * h.rate2;
    return x * h.top_rate;
  }
  function r2(v) { return Math.round(v * 100) / 100; }
  function calculate(R, income, kind, hasHelp) {
    income = Math.max(0, Number(income) || 0);
    var gross = bracketTax(income, R[kind]);
    var off = kind === "resident" ? lito(R, income) : 0;
    var it = Math.max(0, gross - off);
    var levy = kind === "resident" ? medicare(R, income) : 0;
    var loan = hasHelp ? helpRepay(R, income) : 0;
    var total = it + levy + loan;
    return { income: income, income_tax: r2(it), medicare: r2(levy), help: r2(loan),
      total_tax: r2(total), net: r2(income - total), super: r2(income * R.super_rate) };
  }
  root.PayCalc = { calculate: calculate };
  if (typeof module !== "undefined") module.exports = root.PayCalc;

  if (typeof document === "undefined") return;
  var form = document.getElementById("calc");
  if (!form || !root.RATES) return;
  var R = root.RATES;
  var fmt = new Intl.NumberFormat("en-AU", { style: "currency", currency: "AUD", maximumFractionDigits: 0 });
  var f = function (id) { return document.getElementById(id); };

  function annual() {
    var amt = parseFloat(String(f("amount").value).replace(/[^0-9.]/g, "")) || 0;
    var per = f("period").value, hrs = parseFloat(f("hours").value) || 38;
    var mult = { year: 1, month: 12, fortnight: 26, week: 52, hour: 52 * hrs }[per];
    var gross = amt * mult;
    if (f("incsuper").checked) gross = gross / (1 + R.super_rate);
    return gross;
  }
  function run() {
    f("hours-wrap").hidden = f("period").value !== "hour";
    var kind = form.querySelector("input[name=kind]:checked").value;
    var res = calculate(R, annual(), kind, f("help").checked);
    var rows = [["Gross pay", res.income], ["Income tax", -res.income_tax], ["Medicare levy", -res.medicare],
      ["HELP / student loan", -res.help], ["Take-home pay", res.net], ["Super (paid on top)", res.super]];
    var periods = [["Year", 1], ["Month", 12], ["Fortnight", 26], ["Week", 52]];
    var html = "<thead><tr><th></th>" + periods.map(function (p) { return "<th>" + p[0] + "</th>"; }).join("") + "</tr></thead><tbody>";
    rows.forEach(function (row) {
      if (row[0] === "HELP / student loan" && !f("help").checked) return;
      if (row[0] === "Medicare levy" && kind !== "resident") return;
      var cls = row[0] === "Take-home pay" ? ' class="net"' : "";
      html += "<tr" + cls + "><th>" + row[0] + "</th>" + periods.map(function (p) {
        return "<td>" + fmt.format(row[1] / p[1]) + "</td>";
      }).join("") + "</tr>";
    });
    f("result").innerHTML = html + "</tbody>";
    f("headline").textContent = fmt.format(res.net / 26);
    f("headline-sub").textContent = "take-home every fortnight (" + fmt.format(res.net) + " a year). You keep " +
      (res.income ? Math.round(res.net / res.income * 100) : 100) + "% of your pay.";
    try { localStorage.setItem("pc", JSON.stringify({ a: f("amount").value, p: f("period").value, k: kind })); } catch (e) {}
  }
  try {
    var saved = JSON.parse(localStorage.getItem("pc") || "null");
    if (saved && !form.dataset.fixed) {
      f("amount").value = saved.a; f("period").value = saved.p;
      var k = form.querySelector("input[name=kind][value=" + saved.k + "]"); if (k) k.checked = true;
    }
  } catch (e) {}
  form.addEventListener("input", run);
  form.addEventListener("submit", function (e) { e.preventDefault(); run(); });
  run();
})(typeof window !== "undefined" ? window : globalThis);
