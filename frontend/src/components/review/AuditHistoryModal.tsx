"use client";

import React from "react";
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Button,
  Chip,
  Divider,
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
} from "@heroui/react";
import { History, ShieldCheck, CheckCircle2, XCircle, Download } from "lucide-react";
import { AuditLogResponse } from "@/types/api";

interface AuditHistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  auditLogs: AuditLogResponse[];
  reportId: number;
}

export function AuditHistoryModal({
  isOpen,
  onClose,
  auditLogs,
  reportId,
}: AuditHistoryModalProps) {
  const getDecisionBadge = (decision: string) => {
    switch (decision) {
      case "accepted":
        return (
          <Chip
            size="sm"
            color="success"
            variant="flat"
            startContent={<CheckCircle2 className="w-3 h-3" />}
          >
            Accepted
          </Chip>
        );
      case "ignored":
        return (
          <Chip
            size="sm"
            color="danger"
            variant="flat"
            startContent={<XCircle className="w-3 h-3" />}
          >
            Ignored
          </Chip>
        );
      case "exported":
        return (
          <Chip
            size="sm"
            color="primary"
            variant="flat"
            startContent={<Download className="w-3 h-3" />}
          >
            Exported
          </Chip>
        );
      default:
        return (
          <Chip size="sm" variant="flat">
            {decision}
          </Chip>
        );
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      size="2xl"
      scrollBehavior="inside"
      backdrop="blur"
    >
      <ModalContent>
        <ModalHeader className="flex flex-col gap-1 pb-2">
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-primary" />
            <span className="text-base font-semibold text-foreground">
              Clinical Decision Audit Log
            </span>
          </div>
          <p className="text-xs text-foreground-400 font-normal">
            Authoritative immutable record of all physician decisions and exports for report #{reportId}.
          </p>
        </ModalHeader>

        <Divider />

        <ModalBody className="py-4 space-y-4">
          <div className="flex items-center gap-2 p-3 rounded-medium bg-default-50 border border-default-200 text-xs text-foreground-600">
            <ShieldCheck className="w-4 h-4 text-success shrink-0" />
            <span>
              All suggestion acceptances and ignores are explicitly authorized by the attending physician.
            </span>
          </div>

          {auditLogs.length === 0 ? (
            <div className="py-8 text-center text-xs text-foreground-400">
              No audit actions recorded yet. Decisions will appear here as suggestions are reviewed or exported.
            </div>
          ) : (
            <Table
              aria-label="Audit history log table"
              shadow="none"
              className="border border-default-200 dark:border-default-100 rounded-medium"
            >
              <TableHeader>
                <TableColumn>DECISION</TableColumn>
                <TableColumn>TARGET</TableColumn>
                <TableColumn>TIMESTAMP</TableColumn>
              </TableHeader>
              <TableBody>
                {auditLogs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell>{getDecisionBadge(log.decision)}</TableCell>
                    <TableCell>
                      {log.suggestion_id ? (
                        <span className="text-xs font-mono">
                          Suggestion #{log.suggestion_id}
                        </span>
                      ) : (
                        <span className="text-xs text-foreground-400">
                          Final Export
                        </span>
                      )}
                    </TableCell>
                    <TableCell>
                      <span className="text-xs text-foreground-600">
                        {new Date(log.decided_at).toLocaleString()}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </ModalBody>

        <Divider />

        <ModalFooter>
          <Button color="default" variant="flat" size="sm" onPress={onClose}>
            Close
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
