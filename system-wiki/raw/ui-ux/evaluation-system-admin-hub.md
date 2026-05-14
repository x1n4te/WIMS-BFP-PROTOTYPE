The system admin hub UI/UX is bad, what im seeing is just a straight down flow, i want to utilize the whole space and create a HCI UI/UX.

The issues i have found is that the "all synced" line in the top is not placed well, instead of it being a long rectangle in the top, make this a square as named System Integrity in lne with key metrics, but this time it should have graphs on total users as data over time trend chart, active sessions as a bar chart, total api requests as a data over time trend chart. we also need to add VPS resource usage, container status on all containers, PWA sync health, network traffic, and AI on-demand latency.

The system health should also have a fluctuating heart beat trend chart on each active technologies such as Keycloak, Redis, Postgresql.

The Identity Governance should be overhauled, this should be Activity & Governance and there should be tabs on this container that will change what this contains such as users, sessions.

There should be also an dedicated container for the Threats, Audit Logs, then another for settings.

For modals it should be consolidated into one format, when pressing the session icon on the user on the current identity governance container, it opens a modal that list down ip adresses of the connected session and has a terminate all button. make this into redirect to the active sessions. The active sessions should also list down the browser being used and the OS.

There is no pagination applied btw.

the edit action on the identity governance has the region id as decrement and increment, postgres-init already contain the .sql for the regions and cities, so instead of decrement and increment it should be a choice.

The /home should also contain more information, but since this is being used by each roles. i want to include a heat map that is set for their current region only.

also there should also be an additional feature in the system which would be the announce feature that would announce a notification system-wide on the home page, this is useful if we are going to be adding maintenance features and emergency operations that the head would want to announce system-wide.

there are no filters on system audit, threat telemetry, active sessions and on identity governance. The frs-systemmonitoringandhealthdashboard says that the system shall support full-text search across log entires, and the configuration management section is not implemented.



