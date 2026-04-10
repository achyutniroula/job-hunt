import { useState, useEffect } from "react";
import { CANADIAN_CITIES, PROVINCES } from "@/data/canadianCities";

interface Props {
  city: string;
  onChange: (city: string, province: string) => void;
}

export default function CitySelector({ city, onChange }: Props) {
  const [province, setProvince] = useState(() => {
    const match = CANADIAN_CITIES.find((c) => c.city === city);
    return match?.province ?? "Canada";
  });

  const citiesInProvince = CANADIAN_CITIES.filter((c) => c.province === province);

  useEffect(() => {
    const first = citiesInProvince[0];
    if (first && !citiesInProvince.find((c) => c.city === city)) {
      onChange(first.city, province);
    }
  }, [province]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleProvinceChange = (p: string) => {
    setProvince(p);
    const first = CANADIAN_CITIES.find((c) => c.province === p);
    if (first) onChange(first.city, p);
  };

  return (
    <div className="flex gap-2">
      <div className="flex-1">
        <label className="text-[10px] font-manrope font-semibold text-text-muted uppercase tracking-[0.15em] mb-2 block">
          Province
        </label>
        <select
          className="input-base text-sm"
          value={province}
          onChange={(e) => handleProvinceChange(e.target.value)}
        >
          {PROVINCES.map(({ province: p, provinceCode }) => (
            <option key={p} value={p}>
              {p === "Canada" ? "Remote / Canada" : `${p} (${provinceCode})`}
            </option>
          ))}
        </select>
      </div>
      <div className="flex-1">
        <label className="text-[10px] font-manrope font-semibold text-text-muted uppercase tracking-[0.15em] mb-2 block">
          City
        </label>
        <select
          className="input-base text-sm"
          value={city}
          onChange={(e) => onChange(e.target.value, province)}
        >
          {citiesInProvince.map(({ city: c }) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>
    </div>
  );
}
