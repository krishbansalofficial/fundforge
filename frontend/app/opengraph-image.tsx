import { ImageResponse } from "next/og";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt = "FundForge: ten trading days, one recalled borrow, twenty-five million dollars that isn't yours";

export default function OgImage() {
  const days = [12, 13, 14, 15, 16, 17, 18, 19, 20, 21];
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", background: "#e8edf1", color: "#16263a" }}>
        <div style={{ display: "flex", background: "#16263a", padding: "28px 48px", gap: 18 }}>
          {days.map((d) => (
            <div key={d} style={{ display: "flex", flexDirection: "column", color: "#f5f7f9", fontSize: 24, width: 92 }}>
              <span>Day {d}</span>
              <span style={{ color: "#f0c27a", fontSize: 18 }}>{d === 15 ? "Recall" : d === 16 ? "Shock" : d === 20 ? "Dealing" : " "}</span>
            </div>
          ))}
        </div>
        <div style={{ display: "flex", flexDirection: "column", padding: "56px 48px", gap: 24, borderLeft: "14px solid #16263a", margin: "40px 48px" }}>
          <span style={{ fontSize: 30, fontWeight: 700 }}>FundForge</span>
          <span style={{ fontSize: 60, fontWeight: 700, lineHeight: 1.05 }}>Ten trading days. One recalled borrow. $25m that isn&apos;t yours.</span>
        </div>
      </div>
    ),
    size,
  );
}
