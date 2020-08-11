# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import urllib.parse

from odoo import api, SUPERUSER_ID


def migrate_altnames(env):
    config = env["ir.config_parameter"]
    existing = config.search([("key", "=like", "letsencrypt.altname.%")])
    if not existing:
        # We may be migrating from 10.0.2.0.0, in which case
        # letsencrypt.altnames already exists and shouldn't be clobbered.
        return
    domains = existing.mapped("value")
    base_url = config.get_param("web.base.url", "http://localhost:8069")
    base_domain = urllib.parse.urlparse(base_url).hostname
    if (
        domains
        and base_domain
        and base_domain != "localhost"
        and base_domain not in domains
    ):
        domains.insert(0, base_domain)
    config.set_param("letsencrypt.altnames", "\n".join(domains))
    existing.unlink()


def migrate_cron(env):
    # Any interval that was appropriate for the old version is inappropriate
    # for the new one, so it's ok to clobber it.
    # But tweaking it afterwards is fine, so noupdate="1" still makes sense.
    jobs = (
        env["ir.cron"]
        .with_context(active_test=False)
        .search(
            [
                ("ir_actions_server_id.model_id.model", "=", "letsencrypt"),
                ("ir_actions_server_id.code", "=", "model.cron()"),
            ]
        )
    )
    if not jobs:
        # ir.cron._try_lock doesn't handle empty recordsets well
        return
    jobs.write({"interval_type": "days", "interval_number": "1"})
    jobs.mapped("ir_actions_server_id").write({"code": "model._cron()"})


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    migrate_altnames(env)
    migrate_cron(env)
