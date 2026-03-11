import * as t from "io-ts";
import {
    GenericPluginMarkup,
    getTopLevelFields,
    nullable,
} from "tim/plugin/attributes";
import type {ApplicationRef, DoBootstrap} from "@angular/core";
import {Component, NgModule} from "@angular/core";
import {HttpClientModule} from "@angular/common/http";
import {FormsModule} from "@angular/forms";
import {TimUtilityModule} from "tim/ui/tim-utility.module";
import {AngularPluginBase} from "tim/plugin/angular-plugin-base.directive";
import {DialogModule} from "tim/ui/angulardialog/dialog.module";
import {PurifyModule} from "tim/util/purify.module";
import {registerPlugin} from "tim/plugin/pluginRegistry";
import {CommonModule} from "@angular/common";

export interface BotUser {
    username: string;
    tokenUsage: number;
    lastActive: Date;
}

export interface BotConfig {
    contextPath: string;
    tokenLimit: number;
    selectedModel: string;
    mode: "creative" | "summarizing";
}

const PluginMarkupFields = t.intersection([
    t.partial({
        // ei tarvita mitään ainakaan toistaiseksi
    }),
    GenericPluginMarkup,
    t.type({
        // all withDefaults should come here; NOT in t.partial
    }),
]);
const PluginFields = t.intersection([
    getTopLevelFields(PluginMarkupFields),
    t.type({
        state: nullable(t.type({userinput: t.string})),
    }),
]);

type PanelKey = "context" | "tokens" | "model" | "mode" | "users";

@Component({
    selector: "controlpanel-runner",
    template: `
        <div>
            <h4>Hallintapaneeli</h4>

            <!-- Context Path -->
            <div>
                <button class="timButton" (click)="toggle('context')">Context Path</button>
                <div *ngIf="open.context">
                    <label>
                        File path
                        <input
                            type="text"
                            class="form-control"
                            [(ngModel)]="config.contextPath"
                            placeholder="users/mike/personal/training.md"
                        />
                    </label>
                    <button class="timButton" (click)="applyPath()">Apply</button>
                    <p *ngIf="config.contextPath">Active path: <code>{{ config.contextPath }}</code></p>
                </div>
            </div>

            <!-- Token Limit -->
            <div>
                <button class="timButton" (click)="toggle('tokens')">Token Limit</button>
                <div *ngIf="open.tokens">
                    <label>
                        Limit: {{ config.tokenLimit | number }} tokens
                        <input
                            type="range"
                            [(ngModel)]="config.tokenLimit"
                            min="500"
                            max="32000"
                            step="500"
                        />
                    </label>
                </div>
            </div>

            <!-- Model -->
            <div>
                <button class="timButton" (click)="toggle('model')">LLM Model</button>
                <div *ngIf="open.model">
                    <label *ngFor="let model of availableModels">
                        <input
                            type="radio"
                            name="model"
                            [value]="model.id"
                            [(ngModel)]="config.selectedModel"
                        />
                        {{ model.name }}
                    </label>
                </div>
            </div>

            <!-- Mode -->
            <div>
                <button class="timButton" (click)="toggle('mode')">Response Mode</button>
                <div *ngIf="open.mode">
                    <label>
                        <input type="radio" name="mode" value="creative" [(ngModel)]="config.mode" />
                        Creative
                    </label>
                    <label>
                        <input type="radio" name="mode" value="summarizing" [(ngModel)]="config.mode" />
                        Summarizing
                    </label>
                </div>
            </div>

            <!-- Users -->
            <div>
                <button class="timButton" (click)="toggle('users')">Users ({{ users.length }})</button>
                <div *ngIf="open.users">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Username</th>
                                <th>Tokens used</th>
                                <th>Last active</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr *ngFor="let user of users">
                                <td>{{ user.username }}</td>
                                <td>{{ user.tokenUsage | number }}</td>
                                <td>{{ user.lastActive | date:'MMM d, HH:mm' }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Save -->
            <div>
                <button class="timButton" (click)="saveConfig()">Save changes</button>
                <span *ngIf="saved">Changes saved.</span>
            </div>

        </div>
    `,
})
export class TeacherControlPanelComponent extends AngularPluginBase<
    t.TypeOf<typeof PluginMarkupFields>,
    t.TypeOf<typeof PluginFields>,
    typeof PluginFields // missing closing > and {
> {
    getAttributeType() {
        return PluginFields;
    }

    getDefaultMarkup() {
        return {};
    }

    saved = false;

    open: Record<PanelKey, boolean> = {
        context: false,
        tokens: false,
        model: false,
        mode: false,
        users: false,
    };

    config: BotConfig = {
        contextPath: "",
        tokenLimit: 8000,
        selectedModel: "gpt-4o",
        mode: "creative",
    };

    availableModels = [
        {id: "gpt-4o", name: "GPT-4o", tag: "OpenAI"},
        {id: "dummy", name: "Dummy", tag: "Dummy1"},
    ];

    users: BotUser[] = [];

    ngOnInit(): void {
        this.users = [
            {
                username: "lepplaju",
                tokenUsage: 7200,
                lastActive: new Date("2025-03-10T14:22:00"),
            },
            {
                username: "jmalmstr",
                tokenUsage: 3100,
                lastActive: new Date("2025-03-11T09:05:00"),
            },
            {
                username: "toni",
                tokenUsage: 12500,
                lastActive: new Date("2025-03-11T11:47:00"),
            },
            {
                username: "joona",
                tokenUsage: 900,
                lastActive: new Date("2025-03-09T17:33:00"),
            },
        ];
    }

    toggle(key: PanelKey): void {
        this.open[key] = !this.open[key];
    }

    applyPath(): void {
        console.log("Context path set to:", this.config.contextPath);
    }

    getUsagePercent(user: BotUser): number {
        return Math.min((user.tokenUsage / this.config.tokenLimit) * 100, 100);
    }

    saveConfig(): void {
        console.log("Saving config:", this.config);
        this.saved = true;
        setTimeout(() => (this.saved = false), 3000);
    }
}

@NgModule({
    declarations: [TeacherControlPanelComponent],
    imports: [
        CommonModule,
        HttpClientModule,
        FormsModule,
        TimUtilityModule,
        PurifyModule,
        DialogModule,
    ],
    exports: [TeacherControlPanelComponent],
})
export class TeacherControlPanelModule implements DoBootstrap {
    // missing class declaration
    ngDoBootstrap(appRef: ApplicationRef) {}
}

registerPlugin(
    "controlpanel-runner",
    TeacherControlPanelModule,
    TeacherControlPanelComponent
);
