""" SPDX-License-Identifier: Apache-2.0
""" Copyright (c) 2025 OrchIntel Systems Ltd.
""" https://orchintel.com | https://ioa.systems
"""
""" Part of IOA Core (Open Source Edition). See LICENSE at repo root.
"""

"""
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

try:
    from flask import Flask, request, jsonify, current_app
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    logging.getLogger(__name__).warning("Flask not available - HITL endpoints disabled")

from src.ioa.core.governance.policy_engine import ActionRiskLevel, ValidationStatus
from src.ioa.core.governance.system_laws import SystemLawsError

logger = logging.getLogger(__name__)

# In-memory storage for HITL tickets (in production, use database)
_hitl_tickets: Dict[str, Dict[str, Any]] = {}
_hitl_decisions: Dict[str, Dict[str, Any]] = {}


@dataclass
class HITLTicket:
    """Human-in-the-Loop approval ticket."""
    ticket_id: str
    connector_id: str
    action_type: str
    actor_id: str
    required_approvals: List[Dict[str, Any]]
    risk_level: str
    created_at: str
    status: str
    audit_id: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class HITLDecision:
    """Human decision on HITL ticket."""
    decision_id: str
    ticket_id: str
    approver_id: str
    decision: str  # "approved", "rejected", "escalated"
    rationale: str
    timestamp: str
    audit_id: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


def create_hitl_app():
    """Create the HITL Flask application."""
    if not FLASK_AVAILABLE:
        raise ImportError("Flask is required for HITL endpoints")
    
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/hitl/tickets', methods=['GET'])
    def list_tickets():
        """List all HITL tickets."""
        try:
            status_filter = request.args.get('status', 'all')
            
            if status_filter == 'all':
                tickets = list(_hitl_tickets.values())
            else:
                tickets = [
                    t for t in _hitl_tickets.values() 
                    if t['status'] == status_filter
                ]
            
            return jsonify({
                "success": True,
                "tickets": tickets,
                "count": len(tickets),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error listing HITL tickets: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/hitl/tickets/<ticket_id>', methods=['GET'])
    def get_ticket(ticket_id: str):
        """Get a specific HITL ticket."""
        try:
            if ticket_id not in _hitl_tickets:
                return jsonify({
                    "success": False,
                    "error": "Ticket not found"
                }), 404
            
            ticket = _hitl_tickets[ticket_id]
            
            # Get decision if exists
            decision = None
            if ticket_id in _hitl_decisions:
                decision = _hitl_decisions[ticket_id]
            
            return jsonify({
                "success": True,
                "ticket": ticket,
                "decision": decision,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting HITL ticket {ticket_id}: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/hitl/tickets', methods=['POST'])
    def create_ticket():
        """Create a new HITL ticket."""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    "success": False,
                    "error": "No data provided"
                }), 400
            
            # Validate required fields
            required_fields = ['connector_id', 'action_type', 'actor_id', 'required_approvals']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }), 400
            
            # Create ticket
            ticket_id = str(uuid.uuid4())
            audit_id = str(uuid.uuid4())
            
            ticket = HITLTicket(
                ticket_id=ticket_id,
                connector_id=data['connector_id'],
                action_type=data['action_type'],
                actor_id=data['actor_id'],
                required_approvals=data['required_approvals'],
                risk_level=data.get('risk_level', 'medium'),
                created_at=datetime.now(timezone.utc).isoformat(),
                status='pending',
                audit_id=audit_id,
                description=data.get('description'),
                metadata=data.get('metadata', {})
            )
            
            # Store ticket
            _hitl_tickets[ticket_id] = asdict(ticket)
            
            logger.info(f"Created HITL ticket {ticket_id} for action {data['action_type']}")
            
            return jsonify({
                "success": True,
                "ticket_id": ticket_id,
                "audit_id": audit_id,
                "ticket": asdict(ticket),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 201
            
        except Exception as e:
            logger.error(f"Error creating HITL ticket: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/hitl/tickets/<ticket_id>/approve', methods=['POST'])
    def approve_ticket(ticket_id: str):
        """Approve an HITL ticket."""
        try:
            if ticket_id not in _hitl_tickets:
                return jsonify({
                    "success": False,
                    "error": "Ticket not found"
                }), 404
            
            data = request.get_json() or {}
            approver_id = data.get('approver_id', 'unknown')
            rationale = data.get('rationale', 'Approved by human operator')
            
            # Create decision
            decision_id = str(uuid.uuid4())
            audit_id = str(uuid.uuid4())
            
            decision = HITLDecision(
                decision_id=decision_id,
                ticket_id=ticket_id,
                approver_id=approver_id,
                decision='approved',
                rationale=rationale,
                timestamp=datetime.now(timezone.utc).isoformat(),
                audit_id=audit_id,
                metadata=data.get('metadata', {})
            )
            
            # Store decision
            _hitl_decisions[ticket_id] = asdict(decision)
            
            # Update ticket status
            _hitl_tickets[ticket_id]['status'] = 'approved'
            _hitl_tickets[ticket_id]['approved_at'] = datetime.now(timezone.utc).isoformat()
            _hitl_tickets[ticket_id]['approver_id'] = approver_id
            
            logger.info(f"Approved HITL ticket {ticket_id} by {approver_id}")
            
            return jsonify({
                "success": True,
                "decision_id": decision_id,
                "audit_id": audit_id,
                "ticket_status": "approved",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error approving HITL ticket {ticket_id}: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/hitl/tickets/<ticket_id>/reject', methods=['POST'])
    def reject_ticket(ticket_id: str):
        """Reject an HITL ticket."""
        try:
            if ticket_id not in _hitl_tickets:
                return jsonify({
                    "success": False,
                    "error": "Ticket not found"
                }), 404
            
            data = request.get_json() or {}
            approver_id = data.get('approver_id', 'unknown')
            rationale = data.get('rationale', 'Rejected by human operator')
            
            # Create decision
            decision_id = str(uuid.uuid4())
            audit_id = str(uuid.uuid4())
            
            decision = HITLDecision(
                decision_id=decision_id,
                ticket_id=ticket_id,
                approver_id=approver_id,
                decision='rejected',
                rationale=rationale,
                timestamp=datetime.now(timezone.utc).isoformat(),
                audit_id=audit_id,
                metadata=data.get('metadata', {})
            )
            
            # Store decision
            _hitl_decisions[ticket_id] = asdict(decision)
            
            # Update ticket status
            _hitl_tickets[ticket_id]['status'] = 'rejected'
            _hitl_tickets[ticket_id]['rejected_at'] = datetime.now(timezone.utc).isoformat()
            _hitl_tickets[ticket_id]['approver_id'] = approver_id
            
            logger.info(f"Rejected HITL ticket {ticket_id} by {approver_id}")
            
            return jsonify({
                "success": True,
                "decision_id": decision_id,
                "audit_id": audit_id,
                "ticket_status": "rejected",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error rejecting HITL ticket {ticket_id}: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/hitl/override', methods=['POST'])
    def override_action():
        """Override a blocked action with human approval."""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    "success": False,
                    "error": "No data provided"
                }), 400
            
            # Validate required fields
            required_fields = ['action_id', 'actor_id', 'action_type', 'approver_id', 'rationale']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }), 400
            
            # Create override record
            override_id = str(uuid.uuid4())
            audit_id = str(uuid.uuid4())
            
            override_record = {
                "override_id": override_id,
                "action_id": data['action_id'],
                "actor_id": data['actor_id'],
                "action_type": data['action_type'],
                "approver_id": data['approver_id'],
                "rationale": data['rationale'],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "audit_id": audit_id,
                "metadata": data.get('metadata', {}),
                "status": "active"
            }
            
            # Store override (in production, use database)
            # For now, we'll just log it
            logger.info(f"Action override created: {override_id} for action {data['action_id']}")
            
            # PATCH: Cursor-2025-09-08 DISPATCH-OSS-20250907-SMOKETEST-PROVIDER-LIVE-HARDEN-v2
            # Log HITL override with comprehensive audit information
            _log_hitl_override_audit(override_record)
            
            return jsonify({
                "success": True,
                "override_id": override_id,
                "audit_id": audit_id,
                "status": "override_active",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error creating action override: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/hitl/pending', methods=['GET'])
    def get_pending_tickets():
        """Get all pending HITL tickets."""
        try:
            pending_tickets = [
                t for t in _hitl_tickets.values() 
                if t['status'] == 'pending'
            ]
            
            return jsonify({
                "success": True,
                "pending_tickets": pending_tickets,
                "count": len(pending_tickets),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting pending tickets: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/hitl/stats', methods=['GET'])
    def get_hitl_stats():
        """Get HITL statistics."""
        try:
            total_tickets = len(_hitl_tickets)
            pending_tickets = len([t for t in _hitl_tickets.values() if t['status'] == 'pending'])
            approved_tickets = len([t for t in _hitl_tickets.values() if t['status'] == 'approved'])
            rejected_tickets = len([t for t in _hitl_tickets.values() if t['status'] == 'rejected'])
            
            return jsonify({
                "success": True,
                "stats": {
                    "total_tickets": total_tickets,
                    "pending_tickets": pending_tickets,
                    "approved_tickets": approved_tickets,
                    "rejected_tickets": rejected_tickets
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting HITL stats: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    return app


def create_hitl_ticket(connector_id: str, action_type: str, actor_id: str,
                       required_approvals: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
    """Create an HITL ticket programmatically."""
    ticket_id = str(uuid.uuid4())
    audit_id = str(uuid.uuid4())
    
    ticket = HITLTicket(
        ticket_id=ticket_id,
        connector_id=connector_id,
        action_type=action_type,
        actor_id=actor_id,
        required_approvals=required_approvals,
        risk_level=kwargs.get('risk_level', 'medium'),
        created_at=datetime.now(timezone.utc).isoformat(),
        status='pending',
        audit_id=audit_id,
        description=kwargs.get('description'),
        metadata=kwargs.get('metadata', {})
    )
    
    # Store ticket
    _hitl_tickets[ticket_id] = asdict(ticket)
    
    logger.info(f"Created HITL ticket {ticket_id} for action {action_type}")
    
    return {
        "ticket_id": ticket_id,
        "audit_id": audit_id,
        "ticket": asdict(ticket)
    }


def _log_hitl_override_audit(override_record: Dict[str, Any]) -> None:
    """
    Log HITL override with comprehensive audit information.
    
    PATCH: Cursor-2025-09-08 DISPATCH-OSS-20250907-SMOKETEST-PROVIDER-LIVE-HARDEN-v2
    Enhanced audit logging for HITL overrides with required fields.
    
    Args:
        override_record: Dictionary containing override information
    """
    try:
        # Extract required audit fields
        override_used = True
        approver = override_record.get("approver_id", "unknown")
        ttl_minutes = override_record.get("metadata", {}).get("ttl_minutes", 15)
        justification = override_record.get("rationale", "No justification provided")
        
        # Create comprehensive audit log entry
        audit_entry = {
            "audit_type": "hitl_override",
            "override_used": override_used,
            "approver": approver,
            "ttl_minutes": ttl_minutes,
            "justification": justification,
            "override_id": override_record.get("override_id"),
            "action_id": override_record.get("action_id"),
            "actor_id": override_record.get("actor_id"),
            "action_type": override_record.get("action_type"),
            "timestamp": override_record.get("timestamp"),
            "audit_id": override_record.get("audit_id"),
            "metadata": override_record.get("metadata", {})
        }
        
        # Log to structured logger
        logger.info(
            f"HITL Override Audit: {override_record.get('override_id')} | "
            f"Approver: {approver} | TTL: {ttl_minutes}min | "
            f"Justification: {justification} | Action: {override_record.get('action_type')}"
        )
        
        # Write to audit log file
        _write_audit_log(audit_entry)
        
    except Exception as e:
        logger.error(f"Failed to log HITL override audit: {e}")


def _write_audit_log(audit_entry: Dict[str, Any]) -> None:
    """Write audit log entry to file."""
    try:
        import json
        from pathlib import Path
        
        # Create audit log directory
        audit_dir = Path("logs/audit")
        audit_dir.mkdir(parents=True, exist_ok=True)
        
        # Write to audit log file
        audit_file = audit_dir / "hitl_overrides.jsonl"
        with audit_file.open('a') as f:
            f.write(json.dumps(audit_entry) + "\n")
            
    except Exception as e:
        logger.warning(f"Failed to write audit log: {e}")


def create_hitl_override_policy_hook() -> callable:
    """
    Create HITL override policy hook for integration with policy engine.
    
    PATCH: Cursor-2025-09-08 DISPATCH-OSS-20250907-SMOKETEST-PROVIDER-LIVE-HARDEN-v2
    Enhanced policy hook for HITL override integration.
    
    Returns:
        Policy hook function that can be registered with policy engine
    """
    def hitl_override_policy_hook(event: Dict[str, Any]) -> None:
        """Policy hook for HITL override events."""
        try:
            if event.get("event_type") == "hitl_override_created":
                # Log policy event
                logger.info(f"HITL override policy event: {event.get('override_id')}")
                
                # Additional policy processing can be added here
                # e.g., notification, escalation, compliance checks
                
        except Exception as e:
            logger.error(f"HITL override policy hook error: {e}")
    
    return hitl_override_policy_hook


def get_hitl_ticket(ticket_id: str) -> Optional[Dict[str, Any]]:
    """Get an HITL ticket by ID."""
    return _hitl_tickets.get(ticket_id)


def is_ticket_approved(ticket_id: str) -> bool:
    """Check if an HITL ticket has been approved."""
    ticket = _hitl_tickets.get(ticket_id)
    return ticket and ticket.get('status') == 'approved'
