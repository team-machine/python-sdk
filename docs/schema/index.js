"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const glob = require("glob");
const mustache_1 = require("mustache");
const Template_1 = require("../../lib/Template");
const utility_1 = require("../../lib/utility");
class ClassicTemplate extends Template_1.default {
    async getTemplateFiles() {
        return new Promise((resolve, reject) => glob('**/*.mustache', { cwd: __dirname }, (error, files) => error ? reject(error) : resolve(files)));
    }
    serialize(templateData, templateFiles) {
        return mustache_1.render(templateFiles.index, templateData, templateFiles);
    }
    renderDirective(type) {
        return this.renderFile(utility_1.getFilenameOf(type), type);
    }
    renderIndex() {
        return this.renderFile('index.html');
    }
    renderType(type) {
        return this.renderFile(utility_1.getFilenameOf(type), type);
    }
}
exports.default = ClassicTemplate;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiaW5kZXguanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi8uLi8uLi8uLi9zcmMvdGVtcGxhdGUvY2xhc3NpYy9pbmRleC50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiOztBQUFBLDZCQUE2QjtBQUM3Qix1Q0FBa0M7QUFFbEMsaURBQWdFO0FBQ2hFLCtDQUFrRDtBQUdsRCxNQUFxQixlQUFnQixTQUFRLGtCQUFRO0lBQzVDLEtBQUssQ0FBQyxnQkFBZ0I7UUFDM0IsT0FBTyxJQUFJLE9BQU8sQ0FBVyxDQUFDLE9BQU8sRUFBRSxNQUFNLEVBQUUsRUFBRSxDQUFDLElBQUksQ0FDcEQsZUFBZSxFQUNmLEVBQUUsR0FBRyxFQUFFLFNBQVMsRUFBRSxFQUNsQixDQUFDLEtBQUssRUFBRSxLQUFLLEVBQUUsRUFBRSxDQUFDLEtBQUssQ0FBQyxDQUFDLENBQUMsTUFBTSxDQUFDLEtBQUssQ0FBQyxDQUFDLENBQUMsQ0FBQyxPQUFPLENBQUMsS0FBSyxDQUFDLENBQ3pELENBQUMsQ0FBQztJQUNMLENBQUM7SUFFTSxTQUFTLENBQUMsWUFBMkIsRUFBRSxhQUErQjtRQUMzRSxPQUFPLGlCQUFNLENBQUMsYUFBYSxDQUFDLEtBQUssRUFBRSxZQUFZLEVBQUUsYUFBYSxDQUFDLENBQUM7SUFDbEUsQ0FBQztJQUVNLGVBQWUsQ0FBQyxJQUFhO1FBQ2xDLE9BQU8sSUFBSSxDQUFDLFVBQVUsQ0FBQyx1QkFBYSxDQUFDLElBQUksQ0FBQyxFQUFFLElBQUksQ0FBQyxDQUFDO0lBQ3BELENBQUM7SUFFTSxXQUFXO1FBQ2hCLE9BQU8sSUFBSSxDQUFDLFVBQVUsQ0FBQyxZQUFZLENBQUMsQ0FBQztJQUN2QyxDQUFDO0lBRU0sVUFBVSxDQUFDLElBQWE7UUFDN0IsT0FBTyxJQUFJLENBQUMsVUFBVSxDQUFDLHVCQUFhLENBQUMsSUFBSSxDQUFDLEVBQUUsSUFBSSxDQUFDLENBQUM7SUFDcEQsQ0FBQztDQUNGO0FBeEJELGtDQXdCQyJ9