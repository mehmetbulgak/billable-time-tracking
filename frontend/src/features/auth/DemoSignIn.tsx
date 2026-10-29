import { useEffect, useRef } from "react";

import { ErrorState } from "@/shared/components/ErrorState";
import { FullPageLoader } from "@/shared/components/FullPageLoader";

import { useLoginMutation } from "./authApi";

export function DemoSignIn() {
  const [login, { error }] = useLoginMutation();
  const started = useRef(false);
  const signIn = () => void login({ email: "can@northwind.test", password: "billable-demo" });

  useEffect(() => {
    if (!started.current) {
      started.current = true;
      void login({ email: "can@northwind.test", password: "billable-demo" });
    }
  }, [login]);

  return error ? <ErrorState error={error} onRetry={signIn} fullPage /> : <FullPageLoader />;
}
