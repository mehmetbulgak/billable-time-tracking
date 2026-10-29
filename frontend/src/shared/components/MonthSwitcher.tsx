import ChevronLeft from "@mui/icons-material/ChevronLeft";
import ChevronRight from "@mui/icons-material/ChevronRight";
import IconButton from "@mui/material/IconButton";
import Stack from "@mui/material/Stack";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";

import { currentPeriod, periodLabel, shiftPeriod, type Period } from "@/shared/lib/period";

interface MonthSwitcherProps {
  period: Period;
  onChange: (period: Period) => void;
}

export function MonthSwitcher({ period, onChange }: MonthSwitcherProps) {
  const isCurrent = period >= currentPeriod();

  return (
    <Stack direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
      <Tooltip title="Previous month">
        <IconButton
          aria-label="Previous month"
          onClick={() => {
            onChange(shiftPeriod(period, -1));
          }}
        >
          <ChevronLeft />
        </IconButton>
      </Tooltip>
      <Typography variant="subtitle1" sx={{ minWidth: 132, textAlign: "center" }}>
        {periodLabel(period)}
      </Typography>
      <Tooltip title="Next month">
        <span>
          <IconButton
            aria-label="Next month"
            disabled={isCurrent}
            onClick={() => {
              onChange(shiftPeriod(period, 1));
            }}
          >
            <ChevronRight />
          </IconButton>
        </span>
      </Tooltip>
    </Stack>
  );
}
