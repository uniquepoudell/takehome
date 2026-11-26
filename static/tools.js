/* Interactive work tools. Each form has data-tool; results go in .tool-out. */
(function () {
  "use strict";
  if (typeof document === "undefined") return;
  var W = window.WORK || {}, R = window.RATES, P = window.PayCalc;
  var $ = function (f, id) { var el = f.querySelector("#" + id); return el ? el.value : ""; };
  var n = function (f, id) { return parseFloat(String($(f, id)).replace(/[^0-9.\-]/g, "")) || 0; };
  var fmt = new Intl.NumberFormat("en-AU", { style: "currency", currency: "AUD", minimumFractionDigits: 2, maximumFractionDigits: 2 });
  var fmt0 = new Intl.NumberFormat("en-AU", { style: "currency", currency: "AUD", maximumFractionDigits: 0 });
  function table(rows, head) {
    var h = head ? "<thead><tr>" + head.map(function (c) { return "<th>" + c + "</th>"; }).join("") + "</tr></thead>" : "";
    return '<div class="tablewrap"><table class="result">' + h + "<tbody>" + rows.map(function (r) {
      return "<tr" + (r.cls ? ' class="' + r.cls + '"' : "") + "><th>" + r[0] + "</th>" + r.slice(1).map(function (c) { return "<td>" + c + "</td>"; }).join("") + "</tr>";
    }).join("") + "</tbody></table></div>";
  }
  function big(v, sub) { return '<div class="headline"><strong>' + v + "</strong><span>" + sub + "</span></div>"; }
  function lookup(tbl, x) { for (var i = 0; i < tbl.length; i++) if (tbl[i][0] === null || x <= tbl[i][0]) return tbl[i][1]; return 0; }
  function lookupBelow(tbl, x) { for (var i = 0; i < tbl.length; i++) if (tbl[i][0] === null || x < tbl[i][0]) return tbl[i][1]; return 0; }

  var tools = {
    penalty: function (f) {
      var base = n(f, "base"), casual = $(f, "emp") === "casual", total = 0, hours = 0, rows = [];
      ["ord", "eve", "sat", "sun", "ph", "ot1", "ot2"].forEach(function (k) {
        var h = n(f, "h_" + k), m = n(f, "m_" + k);
        if (k === "ord" && casual) m = m * 1.25;
        if (!h) return;
        var pay = h * base * m; total += pay; hours += h;
        rows.push([f.querySelector("#h_" + k).getAttribute("aria-label").replace(" hours", ""), h + " hrs", fmt.format(base * m) + "/hr", fmt.format(pay)]);
      });
      var out = big(fmt.format(total), "before tax for " + hours + " hours (" + fmt.format(hours ? total / hours : 0) + " an hour on average)");
      out += table(rows, ["", "Hours", "Rate", "Pay"]);
      out += '<p class="small">About ' + fmt0.format(total * 52) + " a year if every week is like this. <a href=\"../index.html\">See it after tax →</a></p>";
      return out;
    },
    casual: function (f) {
      var base = n(f, "base"), hrs = n(f, "hours"), ph = n(f, "phdays"), sick = n(f, "sick");
      var day = hrs / 5;
      var casualYear = base * 1.25 * hrs * (52 - 4) - base * 1.25 * day * (ph + sick);
      var permYear = base * hrs * 52;
      var diff = casualYear - permYear;
      var out = big((diff >= 0 ? "Casual earns " : "Permanent earns ") + fmt0.format(Math.abs(diff)) + " more",
        "a year, assuming the casual takes the same 4 weeks off unpaid and isn't paid for " + (ph + sick) + " public holidays and sick days.");
      out += table([["Casual (" + fmt.format(base * 1.25) + "/hr)", fmt0.format(casualYear)], ["Permanent (" + fmt.format(base) + "/hr)", fmt0.format(permYear)]], ["", "Pay a year"]);
      return out;
    },
    leave: function (f) {
      var hrs = n(f, "hours"), wks = n(f, "weeks"), rate = n(f, "rate"), shift = $(f, "shift") === "1", loading = parseFloat($(f, "loading")) || 0;
      var ordinary = hrs * wks;
      var alHours = ordinary * (shift ? 5 : 4) / 52, plHours = ordinary * 10 / 260;
      var alPay = alHours * rate, load = alPay * loading;
      var out = big(alHours.toFixed(1) + " hours of annual leave", "and " + plHours.toFixed(1) + " hours of personal leave for " + wks + " weeks at " + hrs + " hours a week.");
      out += table([["Annual leave pay", fmt.format(alPay)], ["Leave loading", fmt.format(load)], ["Total when you take it", fmt.format(alPay + load)]]);
      return out;
    },
    redundancy: function (f) {
      var yrs = n(f, "years"), wk = n(f, "weekly"), age = n(f, "age"), small = $(f, "small") === "1";
      var notice = yrs <= 0 ? 0 : lookup(W.notice_weeks, yrs);
      if (age > 45 && yrs >= 2) notice += W.notice_over45_extra;
      var red = small ? 0 : lookupBelow(W.redundancy_weeks, yrs);
      var out = big(fmt.format((notice + red) * wk), "minimum notice plus redundancy pay before tax");
      out += table([["Notice (or pay instead)", notice + " weeks", fmt.format(notice * wk)], ["Redundancy pay", red + " weeks", fmt.format(red * wk)]], ["", "Weeks", "Amount"]);
      if (small) out += '<p class="small">Small business employers don\'t have to pay NES redundancy pay.</p>';
      out += '<p class="small">Also paid on leaving: unused annual leave (with loading if your award says so). Unused sick leave is not paid out.</p>';
      return out;
    },
    packaging: function (f) {
      var sal = n(f, "salary"), cap = W.salary_packaging.caps[$(f, "emp")], amt = Math.min(n(f, "amount"), cap.taxable), fee = n(f, "fee"), help = $(f, "help") === "1";
      var before = P.calculate(R, sal, "resident", help);
      var after = P.calculate(R, sal - amt - fee, "resident", false);
      var helpAmt = help ? P.helpRepay(R, sal - amt - fee + amt * W.salary_packaging.gross_up) : 0;
      var netAfter = after.net - helpAmt + amt;
      var gain = netAfter - before.net;
      var out = big(fmt0.format(gain) + " more a year", "about " + fmt0.format(gain / 26) + " a fortnight, by packaging " + fmt0.format(amt) + (n(f, "amount") > cap.taxable ? " (capped at your employer's limit)" : ""));
      out += table([["Taxable income", fmt0.format(sal), fmt0.format(sal - amt - fee)], ["Tax, Medicare" + (help ? " and HELP" : ""), fmt0.format(before.total_tax), fmt0.format(after.total_tax + helpAmt)], ["Packaged benefits", "$0", fmt0.format(amt)], ["Spendable income", fmt0.format(before.net), fmt0.format(netAfter)]], ["", "Without", "With packaging"]);
      return out;
    },
    convert: function (f) {
      var amt = n(f, "amount"), per = $(f, "per"), hrs = n(f, "hours") || 38, days = n(f, "days") || 5;
      var yearly = amt * { hour: hrs * 52, day: days * 52, week: 52, fortnight: 26, month: 12, year: 1 }[per];
      return table([["Hourly", fmt.format(yearly / 52 / hrs)], ["Daily", fmt.format(yearly / 52 / days)], ["Weekly", fmt.format(yearly / 52)], ["Fortnightly", fmt.format(yearly / 26)], ["Monthly", fmt.format(yearly / 12)], ["Yearly", fmt0.format(yearly)]], ["Before tax", ""]);
    }
  };
  Array.prototype.forEach.call(document.querySelectorAll("form[data-tool]"), function (f) {
    var fn = tools[f.getAttribute("data-tool")], out = f.querySelector(".tool-out");
    if (!fn) return;
    var run = function () { try { out.innerHTML = fn(f); } catch (e) { out.textContent = "Check your numbers."; } };
    f.addEventListener("input", run); run();
  });
})();
