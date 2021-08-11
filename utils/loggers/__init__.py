# YOLOv5 experiment logging utils

import warnings
from threading import Thread

import torch
from torch.utils.tensorboard import SummaryWriter

from utils.general import colorstr, emojis
from utils.loggers.wandb.wandb_utils import WandbLogger
from utils.plots import plot_images, plot_results
from utils.torch_utils import de_parallel

LOGGERS = ('csv', 'tb', 'wandb')  # text-file, TensorBoard, Weights & Biases

try:
    import wandb

    assert hasattr(wandb, '__version__')  # verify package import not local dir
except (ImportError, AssertionError):
    wandb = None


class Loggers():
    # YOLOv5 Loggers class
    def __init__(self, save_dir=None, weights=None, opt=None, hyp=None, data_dict=None, logger=None, include=LOGGERS):
        self.save_dir = save_dir
        self.weights = weights
        self.opt = opt
        self.hyp = hyp
        self.data_dict = data_dict
        self.logger = logger  # for printing results to console
        self.include = include
        for k in LOGGERS:
            setattr(self, k, None)  # init empty logger dictionary

    def start(self):
        self.csv = True  # always log to csv

        # Message
        try:
            import wandb
        except ImportError:
            prefix = colorstr('Weights & Biases: ')
            s = f"{prefix}run 'pip install wandb' to automatically track and visualize YOLOv5 🚀 runs (RECOMMENDED)"
            print(emojis(s))

        # TensorBoard
        s = self.save_dir
        if 'tb' in self.include and not self.opt.evolve:
            prefix = colorstr('TensorBoard: ')
            self.logger.info(f"{prefix}Start with 'tensorboard --logdir {s.parent}', view at http://localhost:6006/")
            self.tb = SummaryWriter(str(s))

        # W&B
        try:
            assert 'wandb' in self.include and wandb
            run_id = torch.load(self.weights).get('wandb_id') if self.opt.resume else None
            self.opt.hyp = self.hyp  # add hyperparameters
            self.wandb = WandbLogger(self.opt, s.stem, run_id, self.data_dict)
        except:
            self.wandb = None

        return self

    def on_train_batch_end(self, ni, model, imgs, targets, paths, plots):
        # Callback runs on train batch end
        if plots:
            if ni == 0:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')  # suppress jit trace warning
                    self.tb.add_graph(torch.jit.trace(de_parallel(model), imgs[0:1], strict=False), [])
            if ni < 3:
                f = self.save_dir / f'train_batch{ni}.jpg'  # filename
                Thread(target=plot_images, args=(imgs, targets, paths, f), daemon=True).start()
            if self.wandb and ni == 10:
                files = sorted(self.save_dir.glob('train*.jpg'))
                self.wandb.log({'Mosaics': [wandb.Image(str(f), caption=f.name) for f in files if f.exists()]})

    def on_train_epoch_end(self, epoch):
        # Callback runs on train epoch end
        if self.wandb:
            self.wandb.current_epoch = epoch + 1

    def on_val_batch_end(self, pred, predn, path, names, im):
        # Callback runs on train batch end
        if self.wandb:
            self.wandb.val_one_image(pred, predn, path, names, im)

    def on_val_end(self):
        # Callback runs on val end
        if self.wandb:
            files = sorted(self.save_dir.glob('val*.jpg'))
            self.wandb.log({"Validation": [wandb.Image(str(f), caption=f.name) for f in files]})

    def on_train_val_end(self, mloss, results, lr, epoch, best_fitness, fi):
        # Callback runs on val end during training
        vals = list(mloss) + list(results) + lr
        keys = ['train/box_loss', 'train/obj_loss', 'train/cls_loss',  # train loss
                'metrics/precision', 'metrics/recall', 'metrics/mAP_0.5', 'metrics/mAP_0.5:0.95',  # metrics
                'val/box_loss', 'val/obj_loss', 'val/cls_loss',  # val loss
                'x/lr0', 'x/lr1', 'x/lr2']  # params
        x = {k: v for k, v in zip(keys, vals)}  # dict

        if self.csv:
            file = self.save_dir / 'results.csv'
            n = len(x) + 1  # number of cols
            s = '' if file.exists() else (('%20s,' * n % tuple(['epoch'] + keys)).rstrip(',') + '\n')  # add header
            with open(file, 'a') as f:
                f.write(s + ('%20.5g,' * n % tuple([epoch] + vals)).rstrip(',') + '\n')

        if self.tb:
            for k, v in x.items():
                self.tb.add_scalar(k, v, epoch)  # TensorBoard

        if self.wandb:
            self.wandb.log(x)
            self.wandb.end_epoch(best_result=best_fitness == fi)

    def on_model_save(self, last, epoch, final_epoch, best_fitness, fi):
        # Callback runs on model save event
        if self.wandb:
            if ((epoch + 1) % self.opt.save_period == 0 and not final_epoch) and self.opt.save_period != -1:
                self.wandb.log_model(last.parent, self.opt, epoch, fi, best_model=best_fitness == fi)

    def on_train_end(self, last, best, plots):
        # Callback runs on training end
        if plots:
            plot_results(dir=self.save_dir)  # save results.png
        files = ['results.png', 'confusion_matrix.png', *[f'{x}_curve.png' for x in ('F1', 'PR', 'P', 'R')]]
        files = [(self.save_dir / f) for f in files if (self.save_dir / f).exists()]  # filter
        if self.wandb:
            wandb.log({"Results": [wandb.Image(str(f), caption=f.name) for f in files]})
            wandb.log_artifact(str(best if best.exists() else last), type='model',
                               name='run_' + self.wandb.wandb_run.id + '_model',
                               aliases=['latest', 'best', 'stripped'])
            self.wandb.finish_run()

    def log_images(self, paths):
        # Log images
        if self.wandb:
            self.wandb.log({"Labels": [wandb.Image(str(x), caption=x.name) for x in paths]})
