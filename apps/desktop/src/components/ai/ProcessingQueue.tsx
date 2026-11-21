import React from "react";
import { ListFilter, CheckCircle2, XCircle, Clock, Trash2, ExternalLink } from "lucide-react";
import { useAiJobStore } from "../../stores/aiJobStore";

export const ProcessingQueue: React.FC = () => {
  const { jobHistory } = useAiJobStore();

  return (
    <div className="h-full flex flex-col bg-[#141418] select-none text-xs">
      <div className="h-8 bg-[#1c1c22] border-b border-[#262630] flex items-center justify-between px-3">
        <div className="flex items-center gap-1.5 font-semibold text-white tracking-wide text-[11px]">
          <ListFilter className="w-3.5 h-3.5 text-blue-400" />
          <span>RENDER QUEUE & PROCESSING HISTORY</span>
        </div>
        <span className="text-[10px] text-[#707080]">
          {jobHistory.length} Job{jobHistory.length === 1 ? "" : "s"} Recorded
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {jobHistory.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-[#606070] text-xs space-y-1">
            <Clock className="w-8 h-8 opacity-40 stroke-[1.2]" />
            <span>No background inference jobs have been run yet.</span>
            <span className="text-[10px] text-[#505060]">
              Select a plate in the Media Browser and click "Process CorridorKey 2.0".
            </span>
          </div>
        ) : (
          <div className="space-y-1.5">
            {jobHistory.map((item) => (
              <div
                key={item.jobId}
                className="bg-[#1a1a20] border border-[#282832] rounded p-2 flex items-center justify-between text-xs"
              >
                <div className="flex items-center gap-2.5">
                  {item.status === "completed" ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : item.status === "failed" ? (
                    <XCircle className="w-4 h-4 text-red-400" />
                  ) : (
                    <Clock className="w-4 h-4 text-amber-400" />
                  )}
                  <div>
                    <div className="text-white font-medium">{item.jobId}</div>
                    <div className="text-[10px] text-[#707080] font-mono">{item.timestamp}</div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-mono uppercase font-semibold border ${
                      item.status === "completed"
                        ? "bg-emerald-950 text-emerald-400 border-emerald-800"
                        : "bg-red-950 text-red-400 border-red-800"
                    }`}
                  >
                    {item.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
